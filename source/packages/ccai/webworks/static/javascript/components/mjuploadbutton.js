/*
 * mjuploadbutton.js
 *
 * <mj-upload-button> -- a button-styled control that triggers a
 * file picker AND accepts drag-and-drop file drops. Picks
 * normalize through one event: `mj-upload-select` carries
 * the files that were considered (every offered file with
 * `multiple`, the first one without it) plus the accepted /
 * rejected partitions after `accept` and `max-size` filtering.
 * The accepted files become the selection: they are what `files`
 * returns and what is submitted with the owning form. A pick or
 * drop in which every file is rejected keeps the previous
 * selection.
 *
 * `max-size` is a number of bytes, optionally with a unit suffix:
 * `B`, `KB`, `MB` or `GB` (case-insensitive, 1024-based, so `2MB`
 * is 2,097,152 bytes; `KiB` / `MiB` / `GiB` are accepted as
 * aliases). A value that cannot be read is ignored (no limit) with
 * one console warning.
 *
 * Form participation: the accepted files are published under
 * `name`; `required` makes an empty selection invalid; a form
 * reset clears the selection; an ancestor `<fieldset disabled>`
 * disables the control.
 *
 * Why a dedicated component instead of <mj-button>? Upload
 * needs a real `<input type="file">` so the browser surfaces
 * its native file picker (including the system "Recently
 * accessed" / cloud-storage integrations) and so the control
 * participates in `<form>` submission. The native input also
 * supplies the camera / capture affordance on mobile.
 *
 * Drop targeting: by default the host element is the drop
 * surface. Set `drop-target` to a CSS selector pointing at any
 * ancestor / sibling and that element becomes the drop surface
 * instead.
 *
 * Theming: every visual value resolves through a token
 * (`--mj-upload-button-*`) with mj library fallbacks.
 *
 * Docking + anchoring: inherited from MjElement.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

/*
 * Bytes per `max-size` unit suffix. 1024-based, the same base the
 * library uses when it displays file sizes (mj-dropzone,
 * mj-file-picker).
 */
const SIZE_UNITS = new Map([
    ["b", 1],
    ["kb", 1024],
    ["kib", 1024],
    ["mb", 1024 * 1024],
    ["mib", 1024 * 1024],
    ["gb", 1024 * 1024 * 1024],
    ["gib", 1024 * 1024 * 1024],
]);

/*
 * Read a `max-size` value: a non-negative number of bytes with an
 * optional unit suffix (`200000`, `200KB`, `1.5 MB`). Returns the
 * limit in bytes, 0 for "no limit" (absent, empty or zero), or null
 * when the value cannot be read.
 */
function parseMaxSize(text) {
    let bytes = 0;
    const value = text !== null && text !== undefined ? String(text).trim() : "";
    if (value.length > 0) {
        const match = /^(\d+(?:\.\d+)?)\s*([a-z]*)$/i.exec(value);
        let factor = null;
        if (match !== null) {
            const unit = match[2].toLowerCase();
            if (unit.length === 0) {
                factor = 1;
            } else if (SIZE_UNITS.has(unit) === true) {
                factor = SIZE_UNITS.get(unit);
            }
        }
        if (factor === null) {
            bytes = null;
        } else {
            bytes = Math.floor(parseFloat(match[1]) * factor);
        }
    }
    return bytes;
}

const STYLES = `
:host {
  display: inline-block;
  vertical-align: middle;
  position: relative;
}
:host([block]) { display: block; }

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-2);
  min-height: var(--mj-upload-button-height, var(--mj-control-height-md));
  min-width: var(--mj-target-min);
  padding: 0 var(--mj-space-4);
  font: inherit;
  font-weight: var(--mj-upload-button-font-weight, var(--mj-font-weight-medium));
  line-height: 1;
  color: var(--mj-upload-button-color, var(--mj-text));
  background: var(--mj-upload-button-bg, var(--mj-surface));
  border: 1px solid var(--mj-upload-button-border-color, var(--mj-border-strong));
  border-radius: var(--mj-upload-button-border-radius, var(--mj-radius-md));
  cursor: pointer;
  user-select: none;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease),
              border-color var(--mj-motion-fast) var(--mj-motion-ease);
}

.btn:hover { background: var(--mj-bg-muted); }
.btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-upload-button-focus-ring-color, var(--mj-focus-ring));
  outline-offset: var(--mj-focus-ring-offset);
}

:host([variant="primary"]) .btn {
  color: var(--mj-text-on-accent);
  background: var(--mj-accent);
  border-color: var(--mj-accent);
}
:host([variant="primary"]) .btn:hover {
  background: var(--mj-accent-hover);
  border-color: var(--mj-accent-hover);
}
:host([variant="tertiary"]) .btn {
  background: transparent;
  border-color: transparent;
}
:host([variant="tertiary"]) .btn:hover { background: var(--mj-bg-muted); }

:host([size="sm"]) .btn {
  min-height: var(--mj-control-height-sm);
  padding: 0 var(--mj-space-3);
  font-size: var(--mj-font-size-sm);
}
:host([size="lg"]) .btn {
  min-height: var(--mj-control-height-lg);
  padding: 0 var(--mj-space-5);
  font-size: var(--mj-font-size-lg);
}
:host([block]) .btn { width: 100%; }

:host([icon-only]) .btn { padding: 0; aspect-ratio: 1; }

:host([disabled]) .btn,
.btn:disabled,
:host([loading]) .btn {
  opacity: 0.55;
  pointer-events: none;
  cursor: not-allowed;
}

:host([drag-over]) .btn {
  border-color: var(--mj-upload-button-dragover-border-color, var(--mj-accent));
  background: var(--mj-upload-button-dragover-bg, var(--mj-bg-muted));
}
/* The drag-over background replaces the accent fill, so the text must leave the on-accent colour. */
:host([variant="primary"][drag-over]) .btn {
  color: var(--mj-upload-button-color, var(--mj-text));
}

.file-input {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Name of the selected file, or the number of selected files. */
.summary {
  margin-inline-start: var(--mj-space-2);
  font-size: var(--mj-upload-button-summary-font-size, var(--mj-font-size-sm));
  color: var(--mj-upload-button-summary-color, var(--mj-text-muted));
  overflow-wrap: anywhere;
}
:host([icon-only]) .summary { display: none; }

.spinner {
  width: 1em; height: 1em;
  border: 2px solid currentColor;
  border-inline-end-color: transparent;
  border-radius: var(--mj-radius-circle);
  animation: mj-upload-spin var(--mj-motion-slow) linear infinite;
}
:host(:not([loading])) .spinner { display: none; }
@keyframes mj-upload-spin { to { transform: rotate(360deg); } }

@media (prefers-reduced-motion: reduce) {
  .btn { transition: none; }
  .spinner { animation: none; }
}
`;

export class MjUploadButton extends MjElement {
    static tagName = "mj-upload-button";
    static styles = STYLES;
    static watched = [
        "accept",
        "multiple",
        "variant",
        "size",
        "disabled",
        "loading",
        "name",
        "label",
        "max-size",
        "icon-only",
        "block",
        "drop-target",
        "capture",
        "required",
    ];
    static formAssociated = true;

    constructor() {
        super();
        this._button = null;
        this._input = null;
        this._drop_surface = null;
        this._drop_handlers = null;
        this._internals = null;
        /* The current selection: an array of accepted File objects, or null. */
        this._files = null;
        this._summary = null;
        /* True while an ancestor <fieldset disabled> disables this control. */
        this._form_disabled = false;
        /* The unreadable `max-size` value last reported, so the warning is logged once. */
        this._warned_max_size = null;
        if (typeof this.attachInternals === "function") {
            this._internals = this.attachInternals();
        }
    }

    render() {
        const markup = `
            <button class="btn" part="button" type="button">
                <span class="spinner" part="spinner" aria-hidden="true"></span>
                <slot></slot>
            </button>
            <span class="summary" part="summary" hidden></span>
            <input class="file-input" part="file-input" type="file" tabindex="-1" aria-hidden="true">
        `;
        return markup;
    }

    afterRender() {
        this._button = this.$(".btn");
        this._input = this.$(".file-input");
        this._summary = this.$(".summary");
        if (this._button !== null) {
            this.listen(this._button, "click", (event) => {
                this._on_click(event);
            });
        }
        if (this._input !== null) {
            this.listen(this._input, "change", (event) => {
                this._on_input_change(event);
            });
            /*
             * The hidden input is an implementation detail. Its click
             * (sent by `_on_click` to open the picker) and its native
             * `input` event are composed, so without this they would
             * reach listeners on the host: a host click listener would
             * run twice per activation. The picker still opens; only
             * propagation stops. Selections are reported through
             * `mj-upload-select`.
             */
            this.listen(this._input, "click", (event) => {
                event.stopPropagation();
            });
            this.listen(this._input, "input", (event) => {
                event.stopPropagation();
            });
        }
        this._sync_attrs();
        this._sync_summary();
        this._publish_form_value();
        return;
    }

    /*
     * The drop surface can be any element of the page, so its
     * listeners follow the connection: attached on connect,
     * removed on a real disconnect. A reorder inside the same
     * parent keeps them.
     */
    onConnected() {
        this._detach_drop_handlers();
        this._attach_drop_handlers();
        return;
    }

    onDisconnected() {
        this._detach_drop_handlers();
        return;
    }

    onAttributeChanged(name, oldValue, newValue) {
        if (this._input === undefined || this._input === null) {
            return;
        }
        this._sync_attrs();
        if (name === "drop-target" && this._connected === true) {
            this._detach_drop_handlers();
            this._attach_drop_handlers();
        }
        if (name === "required" || name === "name") {
            this._publish_form_value();
        }
        return;
    }

    /* ----- form-associated custom element callbacks ----- */

    formResetCallback() {
        this.clear();
        return;
    }

    formDisabledCallback(disabled) {
        this._form_disabled = disabled === true;
        this._sync_attrs();
        return;
    }

    /*
     * True when the control takes no input: disabled by its own
     * attribute or by an ancestor <fieldset disabled>, or busy.
     */
    _is_inert() {
        const disabled = this.hasAttribute("disabled") === true || this._form_disabled === true;
        const loading = this.hasAttribute("loading");
        const inert = disabled === true || loading === true;
        return inert;
    }

    _on_click(event) {
        if (this._is_inert() === true) {
            return;
        }
        if (this._input !== null) {
            this._input.click();
        }
        return;
    }

    _on_input_change(event) {
        const files = this._input.files !== null ? Array.from(this._input.files) : [];
        /*
         * The native input keeps its value after a pick, so picking
         * the same file again would fire no change event. The files
         * were copied above; the input can be emptied.
         */
        this._input.value = "";
        this._emit_selection(files, "picker");
        return;
    }

    _emit_selection(files, source) {
        let list = files !== null ? Array.from(files) : [];
        if (this.hasAttribute("multiple") === false && list.length > 1) {
            /* A single-file control takes the first offered file only. */
            list = list.slice(0, 1);
        }
        const accepted = [];
        const rejected = [];
        const accept = this.getAttribute("accept") || "";
        const max_size = this._max_size();
        for (const file of list) {
            const ok_type = this._matches_accept(file, accept);
            const ok_size = max_size <= 0 || file.size <= max_size;
            if (ok_type === true && ok_size === true) {
                accepted.push(file);
            } else {
                const reason = ok_type === false ? "accept" : "max-size";
                rejected.push({ file, reason });
            }
        }
        /*
         * Rejected files are neither kept nor submitted. A pick or
         * drop with no accepted file leaves the previous selection
         * as it is; the event still reports the rejections.
         */
        if (accepted.length > 0) {
            this._files = accepted;
            this._publish_form_value();
            this._sync_summary();
        }
        this.emit(
            "mj-upload-select",
            {
                files: list,
                accepted: accepted,
                rejected: rejected,
                source: source,
            },
            { bubbles: true, composed: true },
        );
        if (accepted.length > 0) {
            announce(t("mj.uploadButton.selected", { count: accepted.length }), "polite");
        }
        return;
    }

    /*
     * The `max-size` limit in bytes; 0 means no limit. An unreadable
     * value is ignored (no limit) and reported once per value.
     */
    _max_size() {
        const text = this.getAttribute("max-size");
        let limit = parseMaxSize(text);
        if (limit === null) {
            if (this._warned_max_size !== text) {
                this._warned_max_size = text;
                console.warn("<mj-upload-button>: max-size is not a size (bytes, or a number with B, KB, MB or GB) and was ignored.", this);
            }
            limit = 0;
        }
        return limit;
    }

    _matches_accept(file, accept) {
        if (accept === null || accept.length === 0) {
            return true;
        }
        const patterns = accept.split(",").map((s) => s.trim()).filter((s) => s.length > 0);
        if (patterns.length === 0) {
            return true;
        }
        const type = (file.type || "").toLowerCase();
        const name = (file.name || "").toLowerCase();
        for (const pattern of patterns) {
            const p = pattern.toLowerCase();
            if (p.startsWith(".") === true) {
                if (name.endsWith(p) === true) {
                    return true;
                }
                continue;
            }
            if (p.endsWith("/*") === true) {
                const prefix = p.slice(0, -1);
                if (type.startsWith(prefix) === true) {
                    return true;
                }
                continue;
            }
            if (p === type) {
                return true;
            }
        }
        return false;
    }

    _publish_form_value() {
        if (this._internals === null) {
            return;
        }
        const name = this.getAttribute("name") || "";
        if (name.length === 0 || this._files === null || this._files.length === 0) {
            this._internals.setFormValue(null);
        } else {
            const form_data = new FormData();
            for (const file of this._files) {
                form_data.append(name, file);
            }
            this._internals.setFormValue(form_data);
        }
        this._refresh_validity();
        return;
    }

    /* `required` makes an empty selection invalid, as for a native file input. */
    _refresh_validity() {
        if (this._internals === null) {
            return;
        }
        const empty = this._files === null || this._files.length === 0;
        const missing = this.hasAttribute("required") === true && empty === true;
        if (missing === true && this._button !== undefined && this._button !== null) {
            this._internals.setValidity({ valueMissing: true }, t("core.required"), this._button);
        } else if (missing === true) {
            this._internals.setValidity({ valueMissing: true }, t("core.required"));
        } else {
            this._internals.setValidity({});
        }
        return;
    }

    /* Show what is selected next to the button: the file name, or the file count. */
    _sync_summary() {
        if (this._summary === undefined || this._summary === null) {
            return;
        }
        const count = this._files !== null ? this._files.length : 0;
        if (count === 0) {
            this._summary.textContent = "";
            this._summary.hidden = true;
        } else {
            this._summary.textContent = count === 1 ? this._files[0].name : t("mj.uploadButton.fileCount", { count: count });
            this._summary.hidden = false;
        }
        return;
    }

    _sync_attrs() {
        const input = this._input;
        if (input === null) {
            return;
        }
        const accept = this.getAttribute("accept");
        if (accept !== null && accept.length > 0) {
            input.setAttribute("accept", accept);
        } else {
            input.removeAttribute("accept");
        }
        if (this.hasAttribute("multiple") === true) {
            input.setAttribute("multiple", "");
        } else {
            input.removeAttribute("multiple");
        }
        const capture = this.getAttribute("capture");
        if (capture !== null && capture.length > 0) {
            input.setAttribute("capture", capture);
        } else {
            input.removeAttribute("capture");
        }
        const name = this.getAttribute("name");
        if (name !== null && name.length > 0) {
            input.setAttribute("name", name);
        } else {
            input.removeAttribute("name");
        }
        const disabled = this.hasAttribute("disabled") === true || this._form_disabled === true;
        if (disabled === true) {
            input.setAttribute("disabled", "");
        } else {
            input.removeAttribute("disabled");
        }
        if (this._button !== null) {
            const label = this.getAttribute("label");
            if (label !== null && label.length > 0) {
                this._button.setAttribute("aria-label", label);
            } else {
                this._button.removeAttribute("aria-label");
            }
            if (disabled === true) {
                this._button.setAttribute("disabled", "");
            } else {
                this._button.removeAttribute("disabled");
            }
            /*
             * While loading the button keeps focus but takes no click, so it
             * is reported as unavailable as well as busy.
             */
            const loading = this.hasAttribute("loading") === true;
            this._button.setAttribute("aria-busy", loading === true ? "true" : "false");
            if (loading === true && disabled === false) {
                this._button.setAttribute("aria-disabled", "true");
            } else {
                this._button.removeAttribute("aria-disabled");
            }
            /*
             * `aria-required` is not allowed on the button role, so the
             * required state is not put on the button: it is enforced
             * through validity (valueMissing, reportValidity()) and the
             * visible label should say that a file is required.
             */
        }
        return;
    }

    _attach_drop_handlers() {
        const selector = this.getAttribute("drop-target");
        let surface = this;
        if (selector !== null && selector.length > 0) {
            const root = this.getRootNode();
            let queried = null;
            try {
                queried = typeof root.querySelector === "function"
                    ? root.querySelector(selector)
                    : document.querySelector(selector);
            } catch (error) {
                /* Not a valid selector: keep the host as the drop surface. */
                console.warn("<mj-upload-button>: drop-target is not a valid CSS selector; the button itself is the drop surface.", this);
                queried = null;
            }
            if (queried !== null) {
                surface = queried;
            }
        }
        this._drop_surface = surface;
        const on_dragover = (event) => {
            if (this._is_inert() === true) {
                return;
            }
            event.preventDefault();
            this.setAttribute("drag-over", "");
            if (event.dataTransfer !== null) {
                event.dataTransfer.dropEffect = "copy";
            }
        };
        const on_dragleave = (event) => {
            if (event.target === surface || event.relatedTarget === null) {
                this.removeAttribute("drag-over");
            }
        };
        const on_drop = (event) => {
            if (this._is_inert() === true) {
                return;
            }
            event.preventDefault();
            this.removeAttribute("drag-over");
            const dt = event.dataTransfer;
            if (dt === null) {
                return;
            }
            const files = dt.files;
            if (files === null || files.length === 0) {
                return;
            }
            this._emit_selection(Array.from(files), "drop");
        };
        surface.addEventListener("dragover", on_dragover);
        surface.addEventListener("dragleave", on_dragleave);
        surface.addEventListener("drop", on_drop);
        this._drop_handlers = { surface, on_dragover, on_dragleave, on_drop };
        return;
    }

    _detach_drop_handlers() {
        const h = this._drop_handlers;
        if (h === null || h === undefined) {
            return;
        }
        h.surface.removeEventListener("dragover", h.on_dragover);
        h.surface.removeEventListener("dragleave", h.on_dragleave);
        h.surface.removeEventListener("drop", h.on_drop);
        this._drop_handlers = null;
        return;
    }

    /*
     * Clear the current selection. Resets the underlying input
     * (so re-selecting the same file triggers a fresh change
     * event) and republishes an empty form value.
     */
    clear() {
        if (this._input !== null) {
            this._input.value = "";
        }
        this._files = null;
        this._publish_form_value();
        this._sync_summary();
        return;
    }

    /* The selected (accepted) files as an array, or null when nothing is selected. */
    get files() {
        return this._files;
    }

    get form() {
        const owner = this._internals !== null ? this._internals.form : null;
        return owner;
    }

    get validity() {
        const state = this._internals !== null ? this._internals.validity : null;
        return state;
    }

    get validationMessage() {
        const message = this._internals !== null ? this._internals.validationMessage : "";
        return message;
    }

    checkValidity() {
        const valid = this._internals !== null ? this._internals.checkValidity() : true;
        return valid;
    }

    reportValidity() {
        const valid = this._internals !== null ? this._internals.reportValidity() : true;
        return valid;
    }

    get required() {
        return this.hasAttribute("required");
    }

    set required(value) {
        if (Boolean(value) === true) {
            this.setAttribute("required", "");
        } else {
            this.removeAttribute("required");
        }
        return;
    }

    get disabled() {
        return this.hasAttribute("disabled");
    }

    set disabled(value) {
        if (Boolean(value) === true) {
            this.setAttribute("disabled", "");
        } else {
            this.removeAttribute("disabled");
        }
        return;
    }

    get multiple() {
        return this.hasAttribute("multiple");
    }

    set multiple(value) {
        if (Boolean(value) === true) {
            this.setAttribute("multiple", "");
        } else {
            this.removeAttribute("multiple");
        }
        return;
    }

    /*
     * Opens the file picker as a user click would (browsers only open it
     * during a user gesture). HTMLElement.click() would only dispatch a
     * click at the host, which never reaches the inner button.
     */
    click() {
        if (this._button !== undefined && this._button !== null) {
            this._button.click();
        }
        return;
    }
}
