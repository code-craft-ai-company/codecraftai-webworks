/*
 * mjdownloadbutton.js
 *
 * <mj-download-button> -- a button-styled control that triggers
 * an HTTP download. Internally it renders a real `<a>` element
 * with the `download` attribute so the browser handles the
 * transfer; consumers can pre-empt this by listening for the
 * cancelable `mj-download-start` event and calling
 * `preventDefault()` to run their own (signed-URL fetch,
 * progress, etc.) flow instead.
 *
 * Why a dedicated component instead of <mj-button>? Download
 * needs real anchor semantics so middle-click / ctrl-click open
 * in a new tab, the URL appears in the browser's download UI,
 * and the `download` attribute supplies the suggested filename.
 *
 * Theming: every visual value resolves through a token
 * (`--mj-download-button-*`) with mj library fallbacks.
 *
 * Docking + anchoring: inherited from MjElement.
 */

import { MjElement } from "../core/mjelement.js";

const STYLES = `
:host {
  display: inline-block;
  vertical-align: middle;
}
:host([block]) { display: block; }

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-2);
  min-height: var(--mj-download-button-height, var(--mj-control-height-md));
  min-width: var(--mj-target-min);
  padding: 0 var(--mj-space-4);
  font: inherit;
  font-weight: var(--mj-download-button-font-weight, var(--mj-font-weight-medium));
  line-height: 1;
  color: var(--mj-download-button-color, var(--mj-text));
  background: var(--mj-download-button-bg, var(--mj-surface));
  border: 1px solid var(--mj-download-button-border-color, var(--mj-border-strong));
  border-radius: var(--mj-download-button-border-radius, var(--mj-radius-md));
  text-decoration: none;
  cursor: pointer;
  user-select: none;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
}

.btn:hover { background: var(--mj-bg-muted); }
.btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-download-button-focus-ring-color, var(--mj-focus-ring));
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
:host([variant="link"]) .btn {
  background: transparent;
  border-color: transparent;
  color: var(--mj-accent);
  padding: 0;
  min-height: 0;
  text-decoration: underline;
}

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

.spinner {
  width: 1em; height: 1em;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: var(--mj-radius-circle);
  animation: mj-download-spin var(--mj-motion-slow) linear infinite;
}
:host(:not([loading])) .spinner { display: none; }
@keyframes mj-download-spin { to { transform: rotate(360deg); } }

@media (prefers-reduced-motion: reduce) {
  .btn { transition: none; }
  .spinner { animation: none; }
}
`;

export class MjDownloadButton extends MjElement {
    static tagName = "mj-download-button";
    static styles = STYLES;
    static watched = [
        "href",
        "filename",
        "variant",
        "size",
        "disabled",
        "loading",
        "icon-only",
        "block",
        "target",
        "rel",
        "label",
    ];

    constructor() {
        super();
        this._anchor = null;
    }

    render() {
        const markup = `
            <a class="btn" part="button">
                <span class="spinner" part="spinner" aria-hidden="true"></span>
                <slot></slot>
            </a>
        `;
        return markup;
    }

    afterRender() {
        this._anchor = this.$(".btn");
        if (this._anchor !== null) {
            this._anchor.addEventListener("click", (event) => {
                this._on_click(event);
            });
        }
        this._sync();
        return;
    }

    onAttributeChanged(name, oldValue, newValue) {
        if (this._anchor === null) {
            return;
        }
        this._sync();
        return;
    }

    _on_click(event) {
        if (this.hasAttribute("disabled") === true || this.hasAttribute("loading") === true) {
            event.preventDefault();
            return;
        }
        const detail = {
            href: this.href,
            filename: this.filename,
        };
        const proceeded = this.emit(
            "mj-download-start",
            detail,
            { bubbles: true, composed: true, cancelable: true },
        );
        if (proceeded === false) {
            event.preventDefault();
        }
        return;
    }

    _sync() {
        const anchor = this._anchor;
        if (anchor === null) {
            return;
        }
        const href = this.href;
        if (href.length > 0) {
            anchor.setAttribute("href", href);
        } else {
            anchor.removeAttribute("href");
        }
        const filename = this.filename;
        if (filename.length > 0) {
            anchor.setAttribute("download", filename);
        } else {
            anchor.setAttribute("download", "");
        }
        const target = this.getAttribute("target");
        if (target !== null && target.length > 0) {
            anchor.setAttribute("target", target);
        } else {
            anchor.removeAttribute("target");
        }
        const rel = this.getAttribute("rel");
        if (rel !== null && rel.length > 0) {
            anchor.setAttribute("rel", rel);
        } else if (target === "_blank") {
            anchor.setAttribute("rel", "noopener noreferrer");
        } else {
            anchor.removeAttribute("rel");
        }
        const label = this.getAttribute("label");
        if (label !== null && label.length > 0) {
            anchor.setAttribute("aria-label", label);
        } else {
            anchor.removeAttribute("aria-label");
        }
        if (this.hasAttribute("disabled") === true) {
            anchor.setAttribute("aria-disabled", "true");
            anchor.setAttribute("tabindex", "-1");
        } else {
            anchor.removeAttribute("aria-disabled");
            anchor.removeAttribute("tabindex");
        }
        return;
    }

    get href() {
        const rtnval = this.getAttribute("href") || "";
        return rtnval;
    }

    set href(value) {
        this.setAttribute("href", String(value));
        return;
    }

    get filename() {
        const rtnval = this.getAttribute("filename") || "";
        return rtnval;
    }

    set filename(value) {
        this.setAttribute("filename", String(value));
        return;
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

    get loading() {
        return this.hasAttribute("loading");
    }

    set loading(value) {
        if (value === true) {
            this.setAttribute("loading", "");
        } else {
            this.removeAttribute("loading");
        }
        return;
    }
}
