/*
 * mjfilepicker.js
 *
 * <mj-file-picker> — drag-and-drop file input with validation, image previews,
 * and optional immediate upload. Form-associated.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

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

.dropzone-icon { font-size: 2rem; margin-bottom: var(--mj-space-2); color: var(--mj-text-muted); }
.dropzone-label { color: var(--mj-text); font-size: var(--mj-font-size-md); margin-bottom: var(--mj-space-1); }
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
  margin-top: var(--mj-space-2);
}
.choose-btn:hover { background: var(--mj-accent-hover); }
.choose-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.file-list {
  margin-top: var(--mj-space-3);
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
  margin-top: var(--mj-space-1);
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
.remove-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.error-msg {
  margin-top: var(--mj-space-2);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-color-danger);
}
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

export class MjFilePicker extends FormControlMixin(MjElement) {
  static tagName = "mj-file-picker";
  static styles = STYLES;
  static watched = ["multiple", "accept", "max-size", "max-files", "disabled", "required", "variant", "upload-url"];

  constructor() {
    super()
    this._initFormControl()
    this._files = []
    this._fileItems = []
    this._nativeInput = null
    this._dragCounter = 0
  }

  render() {
    const dropzoneLabel = this.getAttribute("dropzone-label") || "Drag files here or"
    const chooseLabel = this.getAttribute("label") || "Choose files"
    const markup = `
      <div class="dropzone" part="dropzone" role="region" aria-label="File upload dropzone" tabindex="0">
        <span class="dropzone-icon" part="dropzone-icon" aria-hidden="true">
          <slot name="icon">📁</slot>
        </span>
        <span class="dropzone-label" part="dropzone-label">${dropzoneLabel}</span>
        <span class="dropzone-hint" part="dropzone-hint"><slot name="hint"></slot></span>
        <button class="choose-btn" part="choose-button" type="button">${chooseLabel}</button>
      </div>
      <div class="file-list" part="file-list"></div>
      <div class="error-msg" part="error" role="alert" style="display:none"></div>
    `
    return markup
  }

  afterRender() {
    this._dropzone = this.$(".dropzone")
    this._fileList = this.$(".file-list")
    this._errorMsg = this.$(".error-msg")
    this._chooseBtn = this.$(".choose-btn")

    this._nativeInput = document.createElement("input")
    this._nativeInput.type = "file"
    this._nativeInput.setAttribute("aria-hidden", "true")
    this._nativeInput.style.position = "absolute"
    this._nativeInput.style.width = "1px"
    this._nativeInput.style.height = "1px"
    this._nativeInput.style.overflow = "hidden"
    this._nativeInput.style.clip = "rect(0 0 0 0)"
    this._nativeInput.tabIndex = -1

    if (this.hasAttribute("multiple")) {
      this._nativeInput.multiple = true
    }
    const accept = this.getAttribute("accept") || ""
    if (accept.length > 0) {
      this._nativeInput.accept = accept
    }
    this.appendChild(this._nativeInput)

    this.listen(this._chooseBtn, "click", this._onChooseClick.bind(this))
    this.listen(this._dropzone, "click", this._onDropzoneClick.bind(this))
    this.listen(this._dropzone, "keydown", this._onDropzoneKeydown.bind(this))
    this.listen(this._dropzone, "dragover", this._onDragOver.bind(this))
    this.listen(this._dropzone, "dragenter", this._onDragEnter.bind(this))
    this.listen(this._dropzone, "dragleave", this._onDragLeave.bind(this))
    this.listen(this._dropzone, "drop", this._onDrop.bind(this))
    this.listen(this._nativeInput, "change", this._onNativeChange.bind(this))
    return
  }

  _onChooseClick(event) {
    event.stopPropagation()
    this._nativeInput.click()
    return
  }

  _onDropzoneClick(event) {
    if (event.target === this._chooseBtn) {
      return
    }
    this._nativeInput.click()
    return
  }

  _onDropzoneKeydown(event) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      this._nativeInput.click()
    }
    return
  }

  _onDragOver(event) {
    event.preventDefault()
    return
  }

  _onDragEnter() {
    this._dragCounter = this._dragCounter + 1
    this._dropzone.classList.add("drag-over")
    announce("Drop files here to upload", "polite")
    this.emit("mj-drag-enter", {})
    return
  }

  _onDragLeave() {
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

    const droppedFiles = Array.from(event.dataTransfer.files)
    this._addFiles(droppedFiles)
    return
  }

  _onNativeChange() {
    const selected = Array.from(this._nativeInput.files || [])
    this._addFiles(selected)
    this._nativeInput.value = ""
    return
  }

  _addFiles(newFiles) {
    const maxSize = parseInt(this.getAttribute("max-size") || "0", 10)
    const maxFiles = parseInt(this.getAttribute("max-files") || "0", 10)
    const accept = this.getAttribute("accept") || ""
    const isMultiple = this.hasAttribute("multiple")

    if (isMultiple === false) {
      this._files = []
      this._fileItems = []
    }

    newFiles.forEach((file) => {
      const addEvt = this.emit("mj-file-add", { file: file }, { cancelable: true })
      if (addEvt === false) {
        return
      }

      if (maxSize > 0 && file.size > maxSize) {
        this.emit("mj-file-error", { file: file, error: "size" })
        this._showError(`${file.name} exceeds maximum file size.`)
        return
      }

      if (maxFiles > 0 && this._files.length >= maxFiles) {
        this.emit("mj-file-error", { file: file, error: "count" })
        this._showError(`Maximum number of files (${maxFiles}) reached.`)
        return
      }

      if (accept.length > 0) {
        const acceptTypes = accept.split(",").map((s) => s.trim())
        const typeOk = acceptTypes.some((type) => {
          if (type.startsWith(".")) {
            return file.name.toLowerCase().endsWith(type.toLowerCase())
          }
          if (type.endsWith("/*")) {
            const base = type.slice(0, -2)
            return file.type.startsWith(base)
          }
          return file.type === type
        })
        if (typeOk === false) {
          this.emit("mj-file-error", { file: file, error: "type" })
          this._showError(`${file.name} is not an accepted file type.`)
          return
        }
      }

      this._files.push(file)
      this._fileItems.push({ file: file, status: "ready", progress: 0, id: nextId("mj-fi") })
    })

    this._syncFormValue()
    this._renderFileList()
    this.emit("mj-change", { files: this._files.slice() })

    const uploadUrl = this.getAttribute("upload-url") || ""
    if (uploadUrl.length > 0) {
      this._uploadAll(uploadUrl)
    }
    return
  }

  _syncFormValue() {
    this._setFormValue(this._files.length > 0 ? this._files.map((f) => f.name).join(",") : "")
    return
  }

  _renderFileList() {
    let html = ""
    this._fileItems.forEach((item) => {
      const isImage = item.file.type.startsWith("image/")
      let previewHtml = ""
      if (isImage === true && item.objectUrl !== undefined) {
        previewHtml = `<img class="file-preview" part="file-preview" src="${item.objectUrl}" alt="${item.file.name}" />`
      } else {
        previewHtml = `<span class="file-icon" part="file-preview" aria-hidden="true">📄</span>`
      }

      if (isImage === true && item.objectUrl === undefined) {
        item.objectUrl = URL.createObjectURL(item.file)
        setTimeout(() => this._renderFileList(), 0)
      }

      const statusClass = item.status === "success" ? "success" : (item.status === "error" ? "error" : "")
      const statusText = item.status !== "ready" ? item.status : ""

      html += `<div class="file-item" part="file-item" data-id="${item.id}">
        ${previewHtml}
        <div class="file-info">
          <div class="file-name" part="file-name">${item.file.name}</div>
          <div class="file-size" part="file-size">${formatBytes(item.file.size)}</div>
          ${statusText.length > 0 ? `<div class="file-status ${statusClass}" part="file-status">${statusText}</div>` : ""}
          ${item.status === "uploading" ? `<div class="progress-bar" part="file-progress">
            <div class="progress-fill" style="width:${item.progress}%" role="progressbar"
              aria-valuenow="${item.progress}" aria-valuemin="0" aria-valuemax="100"
              aria-label="${item.file.name} upload progress"></div>
          </div>` : ""}
        </div>
        <button class="remove-btn" part="file-remove" type="button" aria-label="Remove ${item.file.name}" data-id="${item.id}">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M12 4 8 8l4 4-1 1-4-4-4 4-1-1 4-4-4-4 1-1 4 4 4-4z"/>
          </svg>
        </button>
      </div>`
    })
    this._fileList.innerHTML = html

    const removeBtns = this._fileList.querySelectorAll(".remove-btn")
    removeBtns.forEach((btn) => {
      this.listen(btn, "click", () => {
        this._removeFile(btn.dataset.id)
      })
    })
    return
  }

  _removeFile(itemId) {
    const idx = this._fileItems.findIndex((i) => i.id === itemId)
    if (idx < 0) {
      return
    }
    const item = this._fileItems[idx]
    if (item.objectUrl !== undefined) {
      URL.revokeObjectURL(item.objectUrl)
    }
    this._fileItems.splice(idx, 1)
    this._files.splice(idx, 1)
    this._syncFormValue()
    this._renderFileList()
    this.emit("mj-file-remove", { file: item.file })
    this.emit("mj-change", { files: this._files.slice() })
    return
  }

  _showError(msg) {
    this._errorMsg.textContent = msg
    this._errorMsg.style.display = ""
    announce(msg, "assertive")
    setTimeout(() => {
      if (this._errorMsg !== undefined) {
        this._errorMsg.style.display = "none"
      }
    }, 5000)
    return
  }

  _uploadAll(uploadUrl) {
    this._fileItems.forEach((item) => {
      if (item.status !== "ready") {
        return
      }
      item.status = "uploading"
      item.progress = 0

      const formData = new FormData()
      formData.append(this.getAttribute("name") || "file", item.file)

      const xhr = new XMLHttpRequest()
      xhr.open("POST", uploadUrl)

      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable === true) {
          item.progress = Math.round((e.loaded / e.total) * 100)
          this._renderFileList()
          this.emit("mj-upload-progress", {
            file: item.file,
            loaded: e.loaded,
            total: e.total,
            percent: item.progress
          })
        }
      })

      xhr.addEventListener("load", () => {
        item.status = "success"
        item.progress = 100
        this._renderFileList()
        this.emit("mj-upload-success", { file: item.file, response: xhr.responseText })
        announce(`${item.file.name} uploaded`, "polite")
      })

      xhr.addEventListener("error", () => {
        item.status = "error"
        this._renderFileList()
        this.emit("mj-upload-error", { file: item.file, error: new Error("Upload failed") })
        announce(`${item.file.name} upload failed`, "assertive")
      })

      xhr.send(formData)
    })
    return
  }

  _customValidity() {
    const required = this.hasAttribute("required")
    if (required === true && this._files.length === 0) {
      return "At least one file is required."
    }
    return ""
  }

  _validationAnchor() {
    return this._chooseBtn || this
  }

  onFormReset() {
    this._files = []
    this._fileItems = []
    this._syncFormValue()
    this._renderFileList()
    return
  }

  get files() {
    return this._files.slice()
  }

  get fileItems() {
    return this._fileItems.slice()
  }
}
