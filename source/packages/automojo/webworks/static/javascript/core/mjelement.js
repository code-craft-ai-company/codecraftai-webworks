/*
 * mjelement.js
 *
 * MjElement -- the base class for every mj-* web component.
 *
 * Responsibilities shared by all components so individual components never
 * re-implement them:
 *   - Shadow DOM attachment and adoption of the shared base stylesheet plus
 *     the component's own stylesheet (theming hook).
 *   - Reflection between attributes and properties for common state.
 *   - Docking (`dock`) and anchoring (`anchor`) participation in layouts.
 *   - A consistent, namespaced CustomEvent emitter.
 *   - An optional popup context menu (right-click / Shift+F10) that every
 *     component inherits -- see `contextMenu` / `setContextMenu`.
 *   - Deterministic cleanup of listeners/observers on disconnect.
 *
 * Universal requirements (web-component-development-plan.md sec.3) are honored
 * here once, on behalf of all components.
 */

import { sharedBaseSheet } from "./basestyles.js";
import { registerDockChild, unregisterDockChild } from "./anchoring.js";
import { openContextMenu, closeContextMenu } from "./contextmenu.js";

let UID_SEQ = 0;

/*
 * Generate a process-unique id, useful for ARIA wiring (aria-controls,
 * aria-describedby, aria-activedescendant, label association).
 */
export function nextId(prefix) {
  UID_SEQ = UID_SEQ + 1;
  const generated = `${prefix || "mj"}-${UID_SEQ}`;
  return generated;
}

export class MjElement extends HTMLElement {
  /*
   * Components override these three statics.
   *   tagName   -- the custom element name, e.g. "mj-button".
   *   styles    -- a CSS string for the component's shadow root.
   *   watched   -- component-specific attribute names to observe.
   */
  static tagName = "mj-element";
  static styles = "";
  static watched = [];

  /*
   * Attributes every component observes for shared behavior. Combined with the
   * component's own `watched` list.
   */
  static get coreAttributes() {
    const attrs = [
      "dock", "anchor", "theme", "disabled", "hidden", "context-menu"
    ];
    return attrs;
  }

  static get observedAttributes() {
    const combined = [...this.coreAttributes, ...this.watched];
    return combined;
  }

  constructor() {
    super()

    this._connected = false
    this._teardown = []
    this._componentSheet = null

    /* Context-menu state. Items are null until a menu is configured. */
    this._contextMenuItems = null
    this._contextMenuWired = false
    this._onHostContextMenu = this._handleContextMenu.bind(this)
    this._onHostContextKey = this._handleContextKey.bind(this)

    const root = this.attachShadow({ mode: "open" })
    this._adoptStyles(root)
  }

  /*
   * Adopt the shared base stylesheet and the component stylesheet into the
   * shadow root. Custom-property theming tokens inherit through the shadow
   * boundary from the document, so only structural base styles are adopted.
   */
  _adoptStyles(root) {
    const sheets = []

    if (sharedBaseSheet !== null) {
      sheets.push(sharedBaseSheet)
    }

    const cssText = this.constructor.styles
    if (cssText !== null && cssText !== undefined && cssText.length > 0) {
      const sheet = new CSSStyleSheet()
      sheet.replaceSync(cssText)
      this._componentSheet = sheet
      sheets.push(sheet)
    }

    root.adoptedStyleSheets = sheets
    return
  }

  /*
   * Render the component's shadow DOM. Components override `render` to return
   * an HTML string for the initial markup. Called once on first connect.
   */
  render() {
    const markup = ""
    return markup
  }

  connectedCallback() {
    if (this._connected === false) {
      const markup = this.render()
      if (markup !== null && markup !== undefined && markup.length > 0) {
        this.shadowRoot.innerHTML = markup
      }
      this.afterRender()
      this._upgradeProperties()
    }

    this._connected = true

    const dockValue = this.getAttribute("dock")
    if (dockValue !== null) {
      registerDockChild(this)
    }

    this.onConnected()
    return
  }

  disconnectedCallback() {
    unregisterDockChild(this)

    for (let index = 0; index < this._teardown.length; index = index + 1) {
      const dispose = this._teardown[index]
      dispose()
    }
    this._teardown = []

    this._connected = false
    this.onDisconnected()
    return
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === "dock") {
      if (newValue !== null) {
        registerDockChild(this)
      } else {
        unregisterDockChild(this)
      }
    }

    if (name === "theme") {
      this._applyTheme(newValue)
    }

    if (name === "context-menu") {
      this._applyContextMenuAttribute(newValue)
    }

    this.onAttributeChanged(name, oldValue, newValue)
    return
  }

  /*
   * Reclaim properties assigned to this element BEFORE its custom-element
   * definition was registered. A value assigned to e.g. `data` before the
   * library script runs becomes a plain own property that shadows the
   * class accessor, so the setter -- and any redraw it triggers -- never
   * runs. This is the standard custom-element "lazy property" upgrade,
   * applied generically: every own property whose name resolves to an
   * accessor with a setter on the prototype chain is captured, removed,
   * and re-assigned through the setter.
   */
  _upgradeProperties() {
    const ownNames = Object.getOwnPropertyNames(this)

    for (let index = 0; index < ownNames.length; index = index + 1) {
      const name = ownNames[index]
      if (name.startsWith("_") === true) {
        continue
      }

      let descriptor = undefined
      let proto = Object.getPrototypeOf(this)
      while (proto !== null && proto !== HTMLElement.prototype) {
        descriptor = Object.getOwnPropertyDescriptor(proto, name)
        if (descriptor !== undefined) {
          break
        }
        proto = Object.getPrototypeOf(proto)
      }

      const hasSetter = descriptor !== undefined && typeof descriptor.set === "function"
      if (hasSetter === true) {
        const pending = this[name]
        delete this[name]
        this[name] = pending
      }
    }

    return
  }

  /*
   * Mirror the `theme` attribute onto `data-theme` so the token palette is
   * scoped to this component subtree. An empty/absent value inherits the
   * ancestor theme.
   */
  _applyTheme(value) {
    if (value === null || value === undefined || value.length === 0) {
      this.removeAttribute("data-theme")
    } else {
      this.setAttribute("data-theme", value)
    }
    return
  }

  /* ----- lifecycle hooks for components to override ----- */
  afterRender() { return }
  onConnected() { return }
  onDisconnected() { return }
  onAttributeChanged(name, oldValue, newValue) { return }

  /* ----- helpers ----- */

  /*
   * Emit a namespaced CustomEvent. All component events are prefixed `mj-`.
   */
  emit(type, detail, options) {
    const opts = options || {}
    const bubbles = opts.bubbles !== false
    const cancelable = opts.cancelable === true
    const composed = opts.composed !== false

    const event = new CustomEvent(type, {
      detail: detail || {},
      bubbles: bubbles,
      cancelable: cancelable,
      composed: composed
    })

    const notCanceled = this.dispatchEvent(event)
    return notCanceled
  }

  /*
   * Register an event listener that is automatically removed on disconnect.
   */
  listen(target, type, handler, options) {
    target.addEventListener(type, handler, options)
    const dispose = () => {
      target.removeEventListener(type, handler, options)
    }
    this._teardown.push(dispose)
    return dispose
  }

  /*
   * Register an arbitrary teardown callback run on disconnect.
   */
  onTeardown(dispose) {
    this._teardown.push(dispose)
    return
  }

  /* Shadow query helpers. */
  $(selector) {
    const found = this.shadowRoot.querySelector(selector)
    return found
  }

  $all(selector) {
    const nodes = this.shadowRoot.querySelectorAll(selector)
    const list = Array.from(nodes)
    return list
  }

  /* Reflect a boolean attribute from a property value. */
  reflectBoolean(name, value) {
    if (value === true) {
      this.setAttribute(name, "")
    } else {
      this.removeAttribute(name)
    }
    return
  }

  get isDisabled() {
    const disabled = this.hasAttribute("disabled")
    return disabled
  }

  /*
   * Standard `disabled` IDL surface so consumers can read/write
   * the attribute through the property (mirroring the native
   * <button> / <input> contract). The setter toggles the
   * attribute so attributeChangedCallback fires and downstream
   * components update their internal state.
   */
  get disabled() {
    return this.hasAttribute("disabled")
  }

  set disabled(value) {
    this.toggleAttribute("disabled", Boolean(value))
    return
  }

  /* ----- context menu -----
   *
   * Every component inherits a popup context menu. Configure it by setting
   * the `contextMenu` property (or calling `setContextMenu`) with an array
   * of items, or declaratively via the `context-menu` attribute holding a
   * JSON array. An item is { label, value, disabled } or { separator: true }.
   * When the user right-clicks the component (or presses Shift+F10 / the
   * ContextMenu key) the menu opens; choosing an item emits the
   * `mj-context-select` event with { value, item }.
   */

  get contextMenu() {
    return this._contextMenuItems
  }

  set contextMenu(items) {
    this.setContextMenu(items)
    return
  }

  /*
   * Set (or clear, with null) this component's context menu items.
   */
  setContextMenu(items) {
    if (items === null || items === undefined) {
      this._contextMenuItems = null
      return
    }

    if (Array.isArray(items) === false) {
      throw new Error("setContextMenu expects an array of menu items")
    }

    this._contextMenuItems = items
    if (items.length > 0) {
      this._ensureContextMenuWired()
    }
    return
  }

  /*
   * Parse the declarative `context-menu` attribute (a JSON array) and apply
   * it. Malformed JSON is ignored rather than thrown so a bad attribute
   * never breaks the component.
   */
  _applyContextMenuAttribute(value) {
    if (value === null || value === undefined || value.trim().length === 0) {
      this._contextMenuItems = null
      return
    }

    let parsed = null
    try {
      parsed = JSON.parse(value)
    } catch (error) {
      return
    }

    if (Array.isArray(parsed) === true) {
      this.setContextMenu(parsed)
    }
    return
  }

  /*
   * Attach the context-menu trigger listeners to the host element once.
   * The listeners live on the element itself so they survive disconnect /
   * reconnect; the wired guard prevents duplicate registration.
   */
  _ensureContextMenuWired() {
    if (this._contextMenuWired === true) {
      return
    }
    this._contextMenuWired = true
    this.addEventListener("contextmenu", this._onHostContextMenu)
    this.addEventListener("keydown", this._onHostContextKey)
    return
  }

  _handleContextMenu(event) {
    if (this._contextMenuItems === null || this._contextMenuItems.length === 0) {
      return
    }
    event.preventDefault()
    this._openContextMenuAt(event.clientX, event.clientY)
    return
  }

  _handleContextKey(event) {
    const isContextKey =
      event.key === "ContextMenu" ||
      (event.shiftKey === true && event.key === "F10")
    if (isContextKey === false) {
      return
    }
    if (this._contextMenuItems === null || this._contextMenuItems.length === 0) {
      return
    }
    event.preventDefault()

    /* Keyboard invocation: anchor the menu to the element's edge. */
    const rect = this.getBoundingClientRect()
    this._openContextMenuAt(rect.left + 8, rect.bottom)
    return
  }

  /*
   * Open this component's context menu at a viewport coordinate.
   */
  _openContextMenuAt(clientX, clientY) {
    const label = this.getAttribute("context-menu-label")

    const handle = openContextMenu(
      this._contextMenuItems,
      clientX,
      clientY,
      {
        label: label !== null ? label : undefined,
        onSelect: (item) => {
          const value = item !== null ? item.value : undefined
          this.emit("mj-context-select", { value: value, item: item, source: this })
        }
      }
    )
    return handle
  }

  /*
   * Close this component's context menu if it is open.
   */
  closeContextMenu() {
    closeContextMenu()
    return
  }
}
