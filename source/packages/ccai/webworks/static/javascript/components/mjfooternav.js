/*
 * mjfooternav.js
 *
 * <mj-footer-nav> -- site-wide footer with grouped navigation links.
 * Renders a <footer role="contentinfo"> landmark containing <nav> column groups.
 * Handles multi-column layout and optional copyright/legal bar.
 *
 * A click on any link inside the footer (groups, brand, social, legal) is
 * announced with the cancelable `mj-footer-nav-navigate` event through one
 * delegated listener on the host.
 *
 * WAI-ARIA: footer role="contentinfo"; each group is nav aria-label.
 */

import { MjElement } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: block; }

footer {
  background: var(--mj-footer-nav-bg, var(--mj-bg-subtle));
  color: var(--mj-footer-nav-color, var(--mj-text-muted));
  padding: var(--mj-footer-nav-padding, var(--mj-space-8) var(--mj-space-6));
}

.root {
  max-width: 1200px;
  margin: 0 auto;
  container-type: inline-size;
}

.brand-area { margin-block-end: var(--mj-space-6); }

.columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: var(--mj-footer-nav-columns-gap, var(--mj-space-8));
  margin-block-end: var(--mj-space-8);
}
/* A fixed column count (the \`columns\` attribute) applies only while there is room for it. */
.columns[data-fixed] {
  grid-template-columns: repeat(var(--mj-footer-nav-fixed-columns, 1), minmax(0, 1fr));
}
@container (max-width: 560px) {
  .columns[data-fixed] { grid-template-columns: 1fr; }
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
  padding-block-start: var(--mj-space-5);
  border-block-start: var(--mj-footer-nav-legal-border, 1px solid var(--mj-border));
  font-size: var(--mj-footer-nav-legal-font-size, var(--mj-font-size-xs));
  color: var(--mj-text-muted);
}

.social-area { margin-block-end: var(--mj-space-6); }

::slotted(*) { color: inherit; }
`;

const HEADING_SELECTOR = "h1, h2, h3, h4, h5, h6, [role='heading']";

export class MjFooterNav extends MjElement {
  static tagName = "mj-footer-nav";
  static styles = STYLES;
  static watched = ["variant", "columns", "copyright", "nav-label", "heading-level"];

  constructor() {
    super()

    /* Group headings whose aria-level was set from `heading-level`. */
    this._leveledHeadings = []

    /* True while this component (not the author) put data-theme="dark" on the host. */
    this._appliedDarkTheme = false
  }

  render() {
    /* The label and the copyright text are applied in afterRender. */
    const markup = html`
      <footer role="contentinfo">
        <div class="root" part="root">
          <div class="brand-area" part="brand"><slot name="brand"></slot></div>
          <div class="social-area" part="social"><slot name="social"></slot></div>
          <div class="columns" part="columns">
            <div class="group-area" part="group"><slot></slot></div>
          </div>
          <div class="legal" part="legal">
            <span class="copyright-text"></span>
            <slot name="legal"></slot>
          </div>
        </div>
      </footer>
    `
    return markup
  }

  afterRender() {
    this._footer = this.$("footer")
    this._columns = this.$(".columns")
    this._copyrightEl = this.$(".copyright-text")
    this._slot = this.shadowRoot.querySelector("slot:not([name])")

    this.listen(this._slot, "slotchange", this._onSlotChange.bind(this))

    /*
     * One delegated listener: it needs no per-link bookkeeping, keeps working
     * after the footer is moved, and covers links added later or slotted into
     * brand / social / legal.
     */
    this.listen(this, "click", this._onClick.bind(this))

    this._syncLabel()
    this._syncCopyright()
    this._updateColumns()
    this._syncHeadingLevels()
    this._syncVariantTheme()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._columns === undefined || this._columns === null) {
      return
    }

    if (name === "columns") {
      this._updateColumns()
    } else if (name === "copyright") {
      this._syncCopyright()
    } else if (name === "nav-label") {
      this._syncLabel()
    } else if (name === "heading-level") {
      this._syncHeadingLevels()
    } else if (name === "variant" || name === "theme") {
      this._syncVariantTheme()
    }
    return
  }

  _syncLabel() {
    let navLabel = this.getAttribute("nav-label")
    if (navLabel === null || navLabel.length === 0) {
      navLabel = t("mj.footerNav.navLabel")
    }
    this._footer.setAttribute("aria-label", navLabel)
    return
  }

  _syncCopyright() {
    this._copyrightEl.textContent = this._formatCopyright(this.getAttribute("copyright"))
    return
  }

  _formatCopyright(text) {
    if (text === null || text === "") {
      return ""
    }
    const year = new Date().getFullYear()
    if (text.indexOf("©") !== -1) {
      return text
    }
    return `© ${year} ${text}`
  }

  _onSlotChange() {
    this._updateColumns()
    this._syncHeadingLevels()
    return
  }

  /*
   * A fixed column count goes into a custom property; the stylesheet uses it
   * only while the footer is wide enough and stacks the groups below that.
   */
  _updateColumns() {
    const colCount = parseInt(this.getAttribute("columns"), 10)
    if (Number.isNaN(colCount) === false && colCount > 0) {
      this._columns.style.setProperty("--mj-footer-nav-fixed-columns", String(colCount))
      this._columns.setAttribute("data-fixed", "")
    } else {
      this._columns.style.removeProperty("--mj-footer-nav-fixed-columns")
      this._columns.removeAttribute("data-fixed")
    }
    return
  }

  /*
   * `heading-level` (2-6) sets the outline level of the group headings. The
   * headings are the author's own elements, so the level is expressed with
   * aria-level instead of replacing the element.
   */
  _syncHeadingLevels() {
    for (let index = 0; index < this._leveledHeadings.length; index = index + 1) {
      this._leveledHeadings[index].removeAttribute("aria-level")
    }
    this._leveledHeadings = []

    const level = parseInt(this.getAttribute("heading-level"), 10)
    if (Number.isNaN(level) === false && level >= 2 && level <= 6) {
      const groups = this._getGroups()
      for (let index = 0; index < groups.length; index = index + 1) {
        const heading = groups[index].matches(HEADING_SELECTOR) === true
          ? groups[index]
          : groups[index].querySelector(HEADING_SELECTOR)
        if (heading !== null) {
          heading.setAttribute("aria-level", String(level))
          this._leveledHeadings.push(heading)
        }
      }
    }
    return
  }

  /*
   * variant="dark" renders the footer with the dark token palette by scoping
   * data-theme="dark" to this element -- unless the author chose a `theme`,
   * which the base class already mirrors to data-theme.
   */
  _syncVariantTheme() {
    const authorTheme = this.hasAttribute("theme")
    const wantsDark = this.getAttribute("variant") === "dark"

    if (authorTheme === false) {
      if (wantsDark === true) {
        this.setAttribute("data-theme", "dark")
        this._appliedDarkTheme = true
      } else if (this._appliedDarkTheme === true) {
        this.removeAttribute("data-theme")
        this._appliedDarkTheme = false
      }
    } else {
      this._appliedDarkTheme = false
    }
    return
  }

  /*
   * The accessible name of a link group: an explicit label, the group's own
   * aria-label / aria-labelledby, or the text of its heading.
   */
  _groupLabel(group) {
    let label = group.getAttribute("label")

    if (label === null || label.length === 0) {
      const marked = group.querySelector("[data-group-label]")
      label = marked !== null ? marked.textContent.trim() : null
    }
    if (label === null || label.length === 0) {
      label = group.getAttribute("aria-label")
    }
    if (label === null || label.length === 0) {
      const labelledBy = group.getAttribute("aria-labelledby")
      if (labelledBy !== null) {
        const root = group.getRootNode()
        const parts = []
        const ids = labelledBy.split(/\s+/)
        for (let index = 0; index < ids.length; index = index + 1) {
          const referenced = ids[index].length > 0 && typeof root.getElementById === "function"
            ? root.getElementById(ids[index])
            : null
          if (referenced !== null) {
            parts.push(referenced.textContent.trim())
          }
        }
        label = parts.join(" ")
      }
    }
    if (label === null || label.length === 0) {
      const heading = group.querySelector(`${HEADING_SELECTOR}, strong`)
      label = heading !== null ? heading.textContent.trim() : ""
    }
    return label
  }

  _onClick(event) {
    /* The link that was clicked: an <a href>, or an mj-link host carrying the href. */
    const path = event.composedPath()
    let link = null
    for (let index = 0; index < path.length && path[index] !== this && link === null; index = index + 1) {
      const node = path[index]
      if (node instanceof Element && node.hasAttribute("href") === true && node.matches("a, mj-link") === true) {
        link = node
      }
    }
    if (link === null) {
      return
    }

    let groupLabel = ""
    const groups = this._getGroups()
    for (let index = 0; index < groups.length; index = index + 1) {
      if (path.indexOf(groups[index]) !== -1) {
        groupLabel = this._groupLabel(groups[index])
      }
    }

    const proceed = this.emit("mj-footer-nav-navigate", {
      href: link.getAttribute("href") || "",
      group: groupLabel,
      originalEvent: event
    }, { cancelable: true })

    if (proceed === false) {
      event.preventDefault()
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
