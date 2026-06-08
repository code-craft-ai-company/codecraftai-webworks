/*
 * mjfooternav.js
 *
 * <mj-footer-nav> -- site-wide footer with grouped navigation links.
 * Renders a <footer role="contentinfo"> landmark containing <nav> column groups.
 * Handles multi-column layout and optional copyright/legal bar.
 *
 * WAI-ARIA: footer role="contentinfo"; each group is nav aria-label.
 */

import { MjElement } from "../core/mjelement.js";

const STYLES = `
:host { display: block; }

footer {
  background: var(--mj-footer-nav-bg, var(--mj-bg-subtle));
  color: var(--mj-footer-nav-color, var(--mj-text-muted));
  padding: var(--mj-footer-nav-padding, var(--mj-space-8) var(--mj-space-6));
}

.root { max-width: 1200px; margin: 0 auto; }

.brand-area { margin-bottom: var(--mj-space-6); }

.columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: var(--mj-footer-nav-columns-gap, var(--mj-space-8));
  margin-bottom: var(--mj-space-8);
}

:host([variant="minimal"]) .columns {
  grid-template-columns: 1fr;
}
:host([variant="centered"]) .root { text-align: center; }

.group-area { display: contents; }

.legal {
  display: flex;
  align-items: center;
  gap: var(--mj-space-4);
  flex-wrap: wrap;
  padding-top: var(--mj-space-5);
  border-top: var(--mj-footer-nav-legal-border, 1px solid var(--mj-border));
  font-size: var(--mj-footer-nav-legal-font-size, var(--mj-font-size-xs));
  color: var(--mj-text-muted);
}

.social-area { margin-bottom: var(--mj-space-6); }

::slotted(*) { color: inherit; }
`;

export class MjFooterNav extends MjElement {
  static tagName = "mj-footer-nav";
  static styles = STYLES;
  static watched = ["variant", "columns", "copyright", "nav-label", "heading-level"];

  render() {
    const navLabel = this.getAttribute("nav-label") || "Footer";
    const copyright = this.getAttribute("copyright") || "";

    const markup = `
      <footer role="contentinfo" aria-label="${navLabel}">
        <div class="root" part="root">
          <div class="brand-area" part="brand"><slot name="brand"></slot></div>
          <div class="social-area" part="social"><slot name="social"></slot></div>
          <div class="columns" part="columns">
            <div class="group-area" part="group"><slot></slot></div>
          </div>
          <div class="legal" part="legal">
            <span class="copyright-text">${this._formatCopyright(copyright)}</span>
            <slot name="legal"></slot>
          </div>
        </div>
      </footer>
    `;
    return markup
  }

  afterRender() {
    this._columns = this.$(".columns");
    this._copyrightEl = this.$(".copyright-text");
    this._slot = this.shadowRoot.querySelector("slot:not([name])");

    this.listen(this._slot, "slotchange", this._onSlotChange.bind(this));
    this._updateColumns();
    this._wireNavigateEvent();
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "columns" && this._columns !== undefined) {
      this._updateColumns();
    }
    if (name === "copyright" && this._copyrightEl !== undefined) {
      this._copyrightEl.textContent = this._formatCopyright(newValue || "");
    }
    return
  }

  _formatCopyright(text) {
    if (text === null || text === "") {
      return ""
    }
    const year = new Date().getFullYear();
    if (text.indexOf("©") !== -1) {
      return text
    }
    return `© ${year} ${text}`
  }

  _onSlotChange() {
    this._updateColumns();
    this._wireNavigateEvent();
    return
  }

  _updateColumns() {
    const colAttr = this.getAttribute("columns");
    const colCount = colAttr !== null && colAttr !== "0" ? parseInt(colAttr, 10) : 0;
    if (colCount > 0) {
      this._columns.style.gridTemplateColumns = `repeat(${colCount}, 1fr)`;
    } else {
      this._columns.style.gridTemplateColumns = "";
    }
    return
  }

  _wireNavigateEvent() {
    const groups = this._getGroups();
    for (let i = 0; i < groups.length; i = i + 1) {
      const group = groups[i];
      const links = group.querySelectorAll("a");
      for (let j = 0; j < links.length; j = j + 1) {
        const link = links[j];
        if (link.dataset.mjFooterWired !== "true") {
          link.dataset.mjFooterWired = "true";
          this.listen(link, "click", (event) => {
            const groupLabel = group.getAttribute("label") || group.querySelector("[data-group-label]")?.textContent || "";
            this.emit("mj-footer-nav-navigate", {
              href: link.getAttribute("href") || "",
              group: groupLabel,
              originalEvent: event
            }, { cancelable: true });
          });
        }
      }
    }
    return
  }

  _getGroups() {
    if (this._slot === undefined || this._slot === null) {
      return []
    }
    return this._slot.assignedElements({ flatten: true })
  }

  get groups() {
    return this._getGroups()
  }
}
