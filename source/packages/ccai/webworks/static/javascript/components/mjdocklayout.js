/*
 * mjdocklayout.js
 *
 * <mj-dock-layout> -- a container that arranges its children by their `dock`
 * attribute (top, bottom, start, end, fill). Each docked child consumes a band
 * of the remaining space in DOM order; `dock="fill"` children share the
 * leftover rectangle. This is the docking host that powers app shells,
 * inspector panels, toolbars-with-content, and similar layouts.
 *
 * Sizing: a band keeps the `height` (top/bottom) or `width` (start/end) its
 * author gave it, or the size of its content; the layout stretches it across
 * the other axis. A fill child is sized on both axes, so a nested
 * <mj-dock-layout dock="fill"> or <mj-split-pane dock="fill"> gets exactly
 * the remaining rectangle. Padding on the layout insets every band, and the
 * `gap` attribute (or the CSS `gap` property) separates the bands.
 *
 * The layout re-runs when the container or a docked child changes size, when
 * a child is added, removed, hidden or shown, and when the `dock` attribute
 * of any child -- an mj-* component or a plain element -- changes.
 *
 * Children WITHOUT a `dock` attribute are left in normal flow, so the layout
 * can also host anchored (`anchor=...`) children, which position against this
 * container because it establishes a positioning context.
 *
 * `mj-layout` (non-bubbling) fires after every pass that laid the children
 * out; a scheduled pass that finds the layout not rendered (0 x 0, for
 * example inside `display: none`) changes nothing and fires nothing.
 *
 * `disabled` has no meaning for a layout: unlike a control it does not stop
 * pointer input to its content.
 */

import { MjElement } from "../core/mjelement.js";
import { getDockChildren, isDockLayoutStale, layoutDock } from "../core/anchoring.js";

const STYLES = `
:host {
  display: block;
  position: relative;
  inline-size: 100%;
  block-size: 100%;
  overflow: hidden;
  background: var(--mj-bg);
  gap: var(--mj-dock-gap, 0);
}

:host([gap="xs"]) { gap: var(--mj-dock-gap, var(--mj-space-1)); }
:host([gap="sm"]) { gap: var(--mj-dock-gap, var(--mj-space-2)); }
:host([gap="md"]) { gap: var(--mj-dock-gap, var(--mj-space-4)); }
:host([gap="lg"]) { gap: var(--mj-dock-gap, var(--mj-space-5)); }
:host([gap="xl"]) { gap: var(--mj-dock-gap, var(--mj-space-6)); }

/*
 * A dock layout that is itself a band of an outer layout must not claim the
 * whole outer container along the axis it consumes; the author gives it a
 * size there (for example style="height: 3rem" on a dock="top" layout).
 */
:host([dock="top"]),
:host([dock="bottom"]) {
  block-size: auto;
}

:host([dock="start"]),
:host([dock="end"]) {
  inline-size: auto;
}

/* A container: the base control rule must not make its content ignore the pointer. */
:host([disabled]) {
  pointer-events: auto;
  cursor: auto;
}
`;

export class MjDockLayout extends MjElement {
  static tagName = "mj-dock-layout";
  static styles = STYLES;
  static watched = ["gap"];

  constructor() {
    super()
    this._layoutFrame = null
    this._resizeObserver = null
    this._childListObserver = null
    this._attributeObserver = null
    this._observedChildren = []
    this._warnedCollapsed = false
  }

  render() {
    const markup = `<slot></slot>`
    return markup
  }

  onConnected() {
    /*
     * Size changes of the container and of every child. The engine's own
     * writes resize children too; `isDockLayoutStale` filters those out so a
     * pass does not schedule another one.
     */
    if (typeof ResizeObserver === "function") {
      this._resizeObserver = new ResizeObserver(() => {
        if (isDockLayoutStale(this) === true) {
          this.requestLayout()
        }
      })
      this._resizeObserver.observe(this)
    }

    /* Children added or removed, and a direction change on the layout. */
    this._childListObserver = new MutationObserver(() => {
      this.requestLayout()
    })
    this._childListObserver.observe(this, {
      childList: true,
      attributes: true,
      attributeFilter: ["dir"]
    })

    /*
     * `dock` and `hidden` changes on the children themselves. Plain elements
     * do not report attribute changes the way mj-* components do, so every
     * child is observed directly (see `_syncObservedChildren`).
     */
    this._attributeObserver = new MutationObserver(() => {
      this.requestLayout()
    })

    /* Content re-assigned to a <slot> child changes the set of dock children. */
    this.listen(this, "slotchange", () => {
      this.requestLayout()
    })

    this.onTeardown(() => {
      this._stopObserving()
    })

    this._syncObservedChildren()
    this.requestLayout()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "gap") {
      this.requestLayout()
    }
    return
  }

  /*
   * Disconnect every observer and drop the pending layout frame, so a layout
   * that left the document neither runs a pass nor emits `mj-layout`.
   */
  _stopObserving() {
    if (this._layoutFrame !== null) {
      window.cancelAnimationFrame(this._layoutFrame)
      this._layoutFrame = null
    }
    if (this._resizeObserver !== null) {
      this._resizeObserver.disconnect()
      this._resizeObserver = null
    }
    if (this._childListObserver !== null) {
      this._childListObserver.disconnect()
      this._childListObserver = null
    }
    if (this._attributeObserver !== null) {
      this._attributeObserver.disconnect()
      this._attributeObserver = null
    }
    this._observedChildren = []
    return
  }

  /*
   * Keep the resize and attribute observers pointed at the current dock
   * children (direct children, or the elements assigned to a <slot> child).
   * Undocked children are observed as well: gaining a `dock` attribute is
   * one of the changes to notice.
   */
  _syncObservedChildren() {
    const children = getDockChildren(this)
    const previous = this._observedChildren

    let changed = children.length !== previous.length
    for (let index = 0; index < children.length && changed === false; index = index + 1) {
      if (children[index] !== previous[index]) {
        changed = true
      }
    }

    if (changed === false) {
      return
    }

    if (this._attributeObserver !== null) {
      /* A MutationObserver cannot drop a single target; re-observe them all. */
      this._attributeObserver.disconnect()
      for (let index = 0; index < children.length; index = index + 1) {
        this._attributeObserver.observe(children[index], {
          attributes: true,
          attributeFilter: ["dock", "hidden"]
        })
      }
    }

    if (this._resizeObserver !== null) {
      for (let index = 0; index < previous.length; index = index + 1) {
        if (children.indexOf(previous[index]) < 0) {
          this._resizeObserver.unobserve(previous[index])
        }
      }
      for (let index = 0; index < children.length; index = index + 1) {
        if (previous.indexOf(children[index]) < 0) {
          this._resizeObserver.observe(children[index])
        }
      }
    }

    this._observedChildren = children
    return
  }

  /*
   * A dock layout with a definite size on only one axis clips every docked
   * child without any visible hint. Say so once.
   */
  _warnIfCollapsed() {
    if (this._warnedCollapsed === true) {
      return
    }

    const noBlockSize = this.clientHeight === 0 && this.clientWidth > 0
    const noInlineSize = this.clientWidth === 0 && this.clientHeight > 0
    const hasDockedChild = this.querySelector(":scope > [dock]") !== null

    if (hasDockedChild === true && (noBlockSize === true || noInlineSize === true)) {
      this._warnedCollapsed = true
      const axis = noBlockSize === true ? "height" : "width"
      console.warn(
        `[mj-dock-layout] The layout has no ${axis}, so its docked children are clipped. ` +
        `Give it a ${axis}, or place it in a container that has one.`
      )
    }
    return
  }

  /*
   * Coalesce multiple layout requests into one pass on the next animation
   * frame so a burst of mutations does not thrash layout. Requests made
   * while the layout is not in the document are ignored; connecting it runs
   * a pass anyway.
   */
  requestLayout() {
    if (this.isConnected === false || this._layoutFrame !== null) {
      return
    }

    this._layoutFrame = window.requestAnimationFrame(() => {
      this._layoutFrame = null
      if (this.isConnected === false) {
        return
      }
      this._syncObservedChildren()
      const laidOut = layoutDock(this)
      if (laidOut === true) {
        this._warnIfCollapsed()
        this.emit("mj-layout", { container: this }, { bubbles: false })
      }
    })
    return
  }
}
