/*
 * mjdocklayout.js
 *
 * <mj-dock-layout> -- a container that arranges its children by their `dock`
 * attribute (top, bottom, start, end, fill). Each docked child consumes a band
 * of the remaining space in DOM order; `dock="fill"` children share the
 * leftover rectangle. This is the docking host that powers app shells,
 * inspector panels, toolbars-with-content, and similar layouts.
 *
 * Children WITHOUT a `dock` attribute are left in normal flow, so the layout
 * can also host anchored (`anchor=...`) children, which position against this
 * container because it establishes a positioning context.
 */

import { MjElement } from "../core/mjelement.js";
import { layoutDock } from "../core/anchoring.js";

const STYLES = `
:host {
  display: block;
  position: relative;
  inline-size: 100%;
  block-size: 100%;
  overflow: hidden;
  background: var(--mj-bg);
}
`;

export class MjDockLayout extends MjElement {
  static tagName = "mj-dock-layout";
  static styles = STYLES;

  constructor() {
    super()
    this._layoutScheduled = false
    this._resizeObserver = null
    this._mutationObserver = null
  }

  render() {
    const markup = `<slot></slot>`
    return markup
  }

  onConnected() {
    if (typeof ResizeObserver === "function") {
      this._resizeObserver = new ResizeObserver(() => {
        this.requestLayout()
      })
      this._resizeObserver.observe(this)
    }

    this._mutationObserver = new MutationObserver(() => {
      this.requestLayout()
    })
    this._mutationObserver.observe(this, {
      childList: true,
      attributes: true,
      attributeFilter: ["dock"],
      subtree: false
    })

    this.requestLayout()
    return
  }

  onDisconnected() {
    if (this._resizeObserver !== null) {
      this._resizeObserver.disconnect()
      this._resizeObserver = null
    }
    if (this._mutationObserver !== null) {
      this._mutationObserver.disconnect()
      this._mutationObserver = null
    }
    return
  }

  /*
   * Coalesce multiple layout requests into one pass on the next animation
   * frame so a burst of mutations does not thrash layout.
   */
  requestLayout() {
    if (this._layoutScheduled === true) {
      return
    }
    this._layoutScheduled = true
    window.requestAnimationFrame(() => {
      this._layoutScheduled = false
      layoutDock(this)
      this.emit("mj-layout", { container: this }, { bubbles: false })
    })
    return
  }
}
