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
 * Without a usable `href` (absent, or rejected by the URL check)
 * the anchor is still a link for assistive technology and the
 * keyboard: it gets `role="link"` and a tab stop, and Enter
 * activates it, so a listener that produces the file itself on
 * `mj-download-start` works from the keyboard too.
 *
 * Tab stop: the component writes the anchor's `tabindex` only
 * when its state needs one (`-1` while disabled, `0` without an
 * href). A `tabindex` set on the anchor by a managing container
 * -- mj-toolbar's roving tab stop -- is kept across attribute
 * changes and restored when `disabled` is removed. A re-render
 * (reconnect after a removal, locale change) starts from a fresh
 * anchor, so a button moved out of a toolbar does not keep the
 * toolbar's value.
 *
 * Theming: every visual value resolves through a token
 * (`--mj-download-button-*`) with mj library fallbacks.
 *
 * Docking + anchoring: inherited from MjElement.
 */

import { MjElement } from "../core/mjelement.js";
import { safeUrl } from "../core/html.js";

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
  border-inline-end-color: transparent;
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
        /* The rejected href last reported, so the warning is logged once. */
        this._warned_href = null;
        /* The anchor tabindex this component wrote itself, or null. */
        this._own_tabindex = null;
        /* The anchor tabindex a managing container (mj-toolbar) set, or null. */
        this._container_tabindex = null;
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
        /* A new anchor carries no tabindex: neither this component's nor a container's. */
        this._own_tabindex = null;
        this._container_tabindex = null;
        if (this._anchor !== null) {
            this.listen(this._anchor, "click", (event) => {
                this._on_click(event);
            });
            this.listen(this._anchor, "keydown", (event) => {
                this._on_keydown(event);
            });
        }
        this._sync();
        return;
    }

    onAttributeChanged(name, oldValue, newValue) {
        if (this._anchor === undefined || this._anchor === null) {
            return;
        }
        this._sync();
        return;
    }

    /*
     * The URL the inner anchor may carry. `href` can come from user
     * data (a stored attachment link), so a script-bearing scheme
     * such as `javascript:` must never reach the anchor: activating
     * it would run script in the page. Relative URLs and http(s),
     * blob, mailto, tel and sms pass through `safeUrl`; `data:` URLs are
     * also allowed because the anchor always carries `download`, so
     * the browser saves them instead of navigating. Anything else
     * yields the empty string.
     */
    _safe_href() {
        const href = this.href;
        let safe = "";
        if (href.length > 0) {
            safe = safeUrl(href, "");
            if (safe === "") {
                const compact = href.replace(/[\u0000- \u007f-\u009f]/g, "").toLowerCase();
                if (compact.startsWith("data:") === true) {
                    safe = href;
                }
            }
            if (safe === "" && this._warned_href !== href) {
                this._warned_href = href;
                console.warn("<mj-download-button>: href uses a URL scheme that is not allowed and was ignored.", this);
            }
        }
        return safe;
    }

    /*
     * An anchor without `href` has no activation behaviour of its
     * own, so Enter is mapped to a click here, as a native link does
     * it when it has an href.
     */
    _on_keydown(event) {
        const plain = event.altKey === false && event.ctrlKey === false && event.metaKey === false;
        if (event.key === "Enter" && plain === true && this._anchor.hasAttribute("href") === false) {
            event.preventDefault();
            this._anchor.click();
        }
        return;
    }

    _on_click(event) {
        if (this.hasAttribute("disabled") === true || this.hasAttribute("loading") === true) {
            event.preventDefault();
            return;
        }
        const detail = {
            href: this._safe_href(),
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
        const href = this._safe_href();
        const has_href = href.length > 0;
        if (has_href === true) {
            anchor.setAttribute("href", href);
            anchor.removeAttribute("role");
        } else {
            /* An anchor without href has no link role; keep announcing it as one. */
            anchor.removeAttribute("href");
            anchor.setAttribute("role", "link");
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
        const disabled = this.hasAttribute("disabled");
        const loading = this.hasAttribute("loading");

        /*
         * Activation is swallowed while disabled or loading, and
         * assistive technology is told so. A loading button stays
         * in the tab order so its busy state can be discovered; a
         * disabled one leaves it.
         */
        if (disabled === true || loading === true) {
            anchor.setAttribute("aria-disabled", "true");
        } else {
            anchor.removeAttribute("aria-disabled");
        }
        if (loading === true && disabled === false) {
            anchor.setAttribute("aria-busy", "true");
        } else {
            anchor.removeAttribute("aria-busy");
        }
        this._sync_tab_stop(disabled, has_href);
        return;
    }

    /*
     * Decide the anchor's tabindex. A value on the anchor that this
     * component did not write was set by a managing container (the
     * roving tab stop of mj-toolbar) and is remembered. Disabled
     * always takes the anchor out of the tab order; otherwise the
     * container's value wins; without one, an anchor that has no
     * href gets `0` so it stays focusable, and an anchor with href
     * needs none.
     */
    _sync_tab_stop(disabled, has_href) {
        const anchor = this._anchor;
        const current = anchor.getAttribute("tabindex");
        if (current !== null && current !== this._own_tabindex) {
            this._container_tabindex = current;
        }
        let wanted = null;
        let own = null;
        if (disabled === true) {
            wanted = "-1";
            own = "-1";
        } else if (this._container_tabindex !== null) {
            wanted = this._container_tabindex;
        } else if (has_href === false) {
            wanted = "0";
            own = "0";
        }
        if (wanted !== null) {
            anchor.setAttribute("tabindex", wanted);
        } else {
            anchor.removeAttribute("tabindex");
        }
        this._own_tabindex = own;
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
        if (Boolean(value) === true) {
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
        if (Boolean(value) === true) {
            this.setAttribute("loading", "");
        } else {
            this.removeAttribute("loading");
        }
        return;
    }

    /*
     * Focus the inner anchor: it is the control in every state, also
     * when a container's roving tabindex of -1 hides it from the
     * generic focus lookup of MjElement.
     */
    focus(options) {
        if (this._anchor !== undefined && this._anchor !== null && this.hasAttribute("tabindex") === false) {
            this._anchor.focus(options);
        } else {
            super.focus(options);
        }
        return;
    }

    /*
     * Starts the download as a user click would (mj-download-start first).
     * HTMLElement.click() would only dispatch a click at the host, which
     * never reaches the inner link.
     */
    click() {
        if (this._anchor !== undefined && this._anchor !== null) {
            this._anchor.click();
        }
        return;
    }
}
