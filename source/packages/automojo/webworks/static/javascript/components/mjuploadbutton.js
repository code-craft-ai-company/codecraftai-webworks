/*
 * mjuploadbutton.js
 *
 * <mj-upload-button> -- a button-styled control that triggers a
 * file picker AND accepts drag-and-drop file drops. Picks
 * normalize through one event: `mj-upload-select` carries the
 * full FileList plus the accepted/rejected partitions after
 * `accept` and `max-size` filtering.
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
:host([loading]) .btn {
  opacity: 0.55;
  pointer-events: none;
  cursor: not-allowed;
}

:host([drag-over]) .btn {
  border-color: var(--mj-upload-button-dragover-border-color, var(--mj-accent));
  background: var(--mj-upload-button-dragover-bg, var(--mj-bg-accent-subtle, var(--mj-bg-muted)));
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

.spinner {
  width: 1em; height: 1em;
  border: 2px solid currentColor;
  border-right-color: transparent;
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
    ];
    static formAssociated = true;

    constructor() {
        super();
        this._button = null;
        this._input = null;
        this._drop_surface = null;
        this._drop_handlers = null;
        this._internals = null;
        this._files = null;
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
            <input class="file-input" part="file-input" type="file">
        `;
        return markup;
    }

    afterRender() {
        this._button = this.$(".btn");
        this._input = this.$(".file-input");
        if (this._button !== null) {
            this._button.addEventListener("click", (event) => {
                this._on_click(event);
            });
        }
        if (this._input !== null) {
            this._input.addEventListener("change", (event) => {
                this._on_input_change(event);
            });
        }
        this._sync_attrs();
        this._attach_drop_handlers();
        return;
    }

    disconnectedCallback() {
        this._detach_drop_handlers();
        if (typeof super.disconnectedCallback === "function") {
            super.disconnectedCallback();
        }
        return;
    }

    onAttributeChanged(name, oldValue, newValue) {
        if (this._input === null) {
            return;
        }
        this._sync_attrs();
        if (name === "drop-target") {
            this._detach_drop_handlers();
            this._attach_drop_handlers();
        }
        return;
    }

    _on_click(event) {
        if (this.hasAttribute("disabled") === true || this.hasAttribute("loading") === true) {
            return;
        }
        if (this._input !== null) {
            this._input.click();
        }
        return;
    }

    _on_input_change(event) {
        const files = this._input.files;
        this._emit_selection(files, "picker");
        return;
    }

    _emit_selection(files, source) {
        const list = files !== null ? Array.from(files) : [];
        const accepted = [];
        const rejected = [];
        const accept = this.getAttribute("accept") || "";
        const max_size = parseInt(this.getAttribute("max-size") || "0", 10);
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
        this._files = files;
        this._publish_form_value();
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
            announce(
                accepted.length === 1
                    ? "1 file selected"
                    : accepted.length + " files selected",
                "polite",
            );
        }
        return;
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
            return;
        }
        const form_data = new FormData();
        for (const file of Array.from(this._files)) {
            form_data.append(name, file);
        }
        this._internals.setFormValue(form_data);
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
        if (this.hasAttribute("disabled") === true) {
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
            if (this.hasAttribute("disabled") === true) {
                this._button.setAttribute("disabled", "");
            } else {
                this._button.removeAttribute("disabled");
            }
        }
        return;
    }

    _attach_drop_handlers() {
        const selector = this.getAttribute("drop-target");
        let surface = this;
        if (selector !== null && selector.length > 0) {
            const root = this.getRootNode();
            const queried = root.querySelector
                ? root.querySelector(selector)
                : document.querySelector(selector);
            if (queried !== null) {
                surface = queried;
            }
        }
        this._drop_surface = surface;
        const on_dragover = (event) => {
            if (this.hasAttribute("disabled") === true) {
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
            if (this.hasAttribute("disabled") === true) {
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
            this._emit_selection(files, "drop");
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
        return;
    }

    get files() {
        return this._files;
    }

    get disabled() {
        return this.hasAttribute("disabled");
    }

    set disabled(value) {
        if (value === true) {
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
        if (value === true) {
            this.setAttribute("multiple", "");
        } else {
            this.removeAttribute("multiple");
        }
        return;
    }
}
