/*
 * mjcharttitle.js
 *
 * <mj-chart-title> -- a coordinated chart part showing the chart's title
 * (and optional subtitle). It binds to its <mj-chart> controller by the
 * `chart` attribute id or the nearest ancestor, and can be placed anywhere
 * in the document. Slotted text overrides the controller's meta title.
 */

import { MjElement } from "../core/mjelement.js";
import { ChartPart } from "./core/chartpart.js";
import { escapeHtml } from "./core/svgdraw.js";

const STYLES = `
:host { display: block; }
.title {
  font-size: var(--mj-font-size-lg, 1.125rem);
  font-weight: var(--mj-font-weight-bold, 700);
  color: var(--mj-text, #14181f);
}
.subtitle {
  font-size: var(--mj-font-size-sm, 0.875rem);
  color: var(--mj-text-muted, #6b7280);
  margin-top: var(--mj-space-1, 0.25rem);
}
`;


export class MjChartTitle extends ChartPart(MjElement) {
  static tagName = "mj-chart-title";
  static styles = STYLES;
  static watched = ["chart", "text", "subtitle"];

  render() {
    const markup = `
      <div class="title" part="title"></div>
      <div class="subtitle" part="subtitle" hidden></div>
    `
    return markup
  }

  afterRender() {
    this._titleEl = this.$(".title")
    this._subtitleEl = this.$(".subtitle")
    this._renderTitle()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._titleEl !== undefined) {
      this._renderTitle()
    }
    return
  }

  drawPart(model, context) {
    this._renderTitle()
    return
  }

  _renderTitle() {
    const slotted = this.textContent !== null ? this.textContent.trim() : ""
    let title = this.getAttribute("text")
    if (title === null && slotted.length > 0) {
      title = slotted
    }
    if (title === null && this._lastModel !== null) {
      const meta = this._lastModel.meta
      title = meta !== undefined && meta.title !== undefined ? meta.title : ""
    }
    this._titleEl.textContent = title || ""

    const subtitle = this.getAttribute("subtitle")
    if (subtitle !== null && subtitle.length > 0) {
      this._subtitleEl.textContent = subtitle
      this._subtitleEl.hidden = false
    } else {
      this._subtitleEl.hidden = true
    }
    return
  }
}
