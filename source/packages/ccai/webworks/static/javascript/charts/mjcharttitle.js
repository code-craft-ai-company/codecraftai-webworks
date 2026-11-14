/*
 * mjcharttitle.js
 *
 * <mj-chart-title> -- a coordinated chart part showing the chart's title
 * (and optional subtitle). It binds to its <mj-chart> controller by the
 * `chart` attribute id or the nearest ancestor, and can be placed anywhere
 * in the document.
 *
 * The title text is, in order: the `text` attribute, the element's own
 * content (shown through a slot, so later edits and rich markup appear as
 * written), then the chart data's meta.title. Content counts when it holds
 * non-blank text or any element, so a title that is only an icon or an
 * <img alt> is shown too; the text the chart takes as its name is the
 * content's text alternative (text, an image's `alt`, an element's
 * `aria-label`, leaving out `hidden` / `aria-hidden` content). The
 * subtitle is the `subtitle` attribute, else meta.subtitle.
 *
 * `level` (1-6) exposes the title as a heading of that level. The bound
 * chart takes this title as its accessible name when it has no `label`.
 */

import { MjElement } from "../core/mjelement.js";
import { ChartPart } from "./core/chartpart.js";

const STYLES = `
:host { display: block; }
.title {
  font-size: var(--mj-chart-title-font-size, var(--mj-font-size-lg, 1.125rem));
  font-weight: var(--mj-font-weight-bold, 700);
  color: var(--mj-chart-title-color, var(--mj-text, #14181f));
}
.subtitle {
  font-size: var(--mj-font-size-sm, 0.875rem);
  color: var(--mj-text-muted, #5f6673);
  margin-block-start: var(--mj-space-1, 0.25rem);
}
`;

/* Elements that never render, so they are not title content. */
const NON_CONTENT_ELEMENTS = ["script", "style", "template"];

/* Attributes of descendants that change the content's text alternative. */
const TEXT_ALTERNATIVE_ATTRIBUTES = ["alt", "aria-label", "aria-hidden", "hidden"];


/*
 * Whether a node of the title's light DOM is content that is shown: a
 * text node with non-blank text, or an element that renders.
 */
function isShownContent(node) {
  let shown = false
  if (node.nodeType === Node.TEXT_NODE) {
    shown = node.data.trim().length > 0
  } else if (node.nodeType === Node.ELEMENT_NODE) {
    shown = NON_CONTENT_ELEMENTS.indexOf(node.localName) < 0 && node.hasAttribute("hidden") === false
  }
  return shown
}


/*
 * The text alternative of a light-DOM node, as assistive technology would
 * read it: text as written, an element's non-blank `aria-label`, an
 * image's `alt`, an SVG's <title>; content that is `hidden`,
 * `aria-hidden="true"` or never rendered gives nothing.
 */
function textAlternative(node) {
  let text = ""
  if (node.nodeType === Node.TEXT_NODE) {
    text = node.data
  } else if (node.nodeType === Node.ELEMENT_NODE) {
    const label = node.getAttribute("aria-label")
    if (NON_CONTENT_ELEMENTS.indexOf(node.localName) >= 0 || node.hasAttribute("hidden") === true ||
        node.getAttribute("aria-hidden") === "true") {
      text = ""
    } else if (label !== null && label.trim().length > 0) {
      text = ` ${label} `
    } else if (node.localName === "br") {
      text = " "
    } else if (node.localName === "img" || node.localName === "area") {
      const alt = node.getAttribute("alt")
      text = alt !== null ? ` ${alt} ` : ""
    } else if (node.localName === "svg") {
      const svgTitle = Array.from(node.children).find((child) => child.localName === "title")
      text = svgTitle !== undefined ? ` ${svgTitle.textContent} ` : ""
    } else {
      const parts = []
      for (let index = 0; index < node.childNodes.length; index = index + 1) {
        parts.push(textAlternative(node.childNodes[index]))
      }
      text = parts.join("")
    }
  }
  return text
}


export class MjChartTitle extends ChartPart(MjElement) {
  static tagName = "mj-chart-title";
  static styles = STYLES;
  static watched = ["chart", "text", "subtitle", "level"];

  constructor() {
    super()
    this._contentObserver = null
    this._titleText = ""
  }

  render() {
    const markup = `
      <div class="title" part="title"><slot></slot><span data-title-text hidden></span></div>
      <div class="subtitle" part="subtitle" hidden></div>
    `
    return markup
  }

  afterRender() {
    this._titleEl = this.$(".title")
    this._slotEl = this.$("slot")
    this._textEl = this.$("[data-title-text]")
    this._subtitleEl = this.$(".subtitle")
    this._renderTitle()
    return
  }

  onPartConnected() {
    /*
     * Edits to the element's own content are picked up as they happen,
     * including an image's `alt` or a label that changes.
     */
    if (typeof MutationObserver === "function") {
      const observer = new MutationObserver(() => {
        this._renderTitle()
      })
      observer.observe(this, {
        childList: true,
        characterData: true,
        subtree: true,
        attributes: true,
        attributeFilter: TEXT_ALTERNATIVE_ATTRIBUTES
      })
      this._contentObserver = observer
      this.onTeardown(() => {
        observer.disconnect()
      })
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    super.onAttributeChanged(name, oldValue, newValue)
    if (this._titleEl === undefined || this._titleEl === null) {
      return
    }
    this._renderTitle()
    return
  }

  drawPart(model, context) {
    if (this._titleEl === undefined || this._titleEl === null) {
      return
    }
    this._renderTitle()
    return
  }

  /* The title text currently shown; the bound chart uses it as its name. */
  get chartLabel() {
    return this._titleText
  }

  _renderTitle() {
    const meta = this._lastModel !== null && this._lastModel.meta !== undefined &&
      this._lastModel.meta !== null ? this._lastModel.meta : {}

    const attributeText = this.getAttribute("text")

    let title = ""
    let fromSlot = false
    if (attributeText !== null) {
      title = attributeText
    } else if (this._hasOwnContent() === true) {
      title = this._ownContentText()
      fromSlot = true
    } else if (meta.title !== undefined && meta.title !== null) {
      title = String(meta.title)
    }

    /* Own content shows through the slot; any other source as plain text. */
    this._slotEl.hidden = fromSlot === false
    this._textEl.hidden = fromSlot === true
    const shownText = fromSlot === true ? "" : title
    if (this._textEl.textContent !== shownText) {
      this._textEl.textContent = shownText
    }

    const level = Number(this.getAttribute("level"))
    if (Number.isInteger(level) === true && level >= 1 && level <= 6) {
      this._titleEl.setAttribute("role", "heading")
      this._titleEl.setAttribute("aria-level", String(level))
    } else {
      this._titleEl.removeAttribute("role")
      this._titleEl.removeAttribute("aria-level")
    }

    let subtitle = this.getAttribute("subtitle")
    if (subtitle === null && meta.subtitle !== undefined && meta.subtitle !== null) {
      subtitle = String(meta.subtitle)
    }
    if (subtitle !== null && subtitle.length > 0) {
      this._subtitleEl.textContent = subtitle
      this._subtitleEl.hidden = false
    } else {
      this._subtitleEl.textContent = ""
      this._subtitleEl.hidden = true
    }

    const changed = title !== this._titleText
    this._titleText = title
    if (changed === true && this.controller !== null &&
        typeof this.controller.refreshLabel === "function") {
      this.controller.refreshLabel()
    }
    return
  }

  /*
   * True when the element has content of its own to show: non-blank text
   * or any rendering element (an icon, an <img alt>), not only whitespace.
   */
  _hasOwnContent() {
    const nodes = this.childNodes
    let found = false
    for (let index = 0; index < nodes.length && found === false; index = index + 1) {
      found = isShownContent(nodes[index])
    }
    return found
  }

  /*
   * The text alternative of the element's own content with runs of
   * whitespace collapsed; "" for purely decorative content.
   */
  _ownContentText() {
    const parts = []
    for (let index = 0; index < this.childNodes.length; index = index + 1) {
      parts.push(textAlternative(this.childNodes[index]))
    }
    const text = parts.join("").replace(/\s+/g, " ").trim()
    return text
  }
}
