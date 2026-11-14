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
 *   - Attribute changes that arrive before the first render are delivered
 *     again once the shadow DOM exists.
 *   - A reorder inside the same parent does not tear the component down.
 *   - A locale change (`setLocale` / `registerStrings` in core/intl.js)
 *     renders every connected component again, so strings read through
 *     `t()` and locale-aware formatting follow the new locale (see
 *     `onLocaleChanged`).
 *
 * Universal requirements (web-component-development-plan.md sec.3) are honored
 * here once, on behalf of all components.
 */

import { sharedBaseSheet } from "./basestyles.js";
import { registerDockChild, unregisterDockChild } from "./anchoring.js";
import { openContextMenu, closeContextMenu } from "./contextmenu.js";
import { onLocaleChange } from "./intl.js";

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

    /* True once render() + afterRender() have run for the first time. */
    this._rendered = false

    /* Attribute changes seen before the first render, replayed after it. */
    this._pendingAttributeChanges = []

    /* Set while a disconnect waits to learn whether it was only a move. */
    this._disconnectPending = false
    this._lastParent = null

    /* Native events currently travelling through the shadow root, by type. */
    this._inflightNativeEvents = {}

    /* Context-menu state. Items are null until a menu is configured. */
    this._contextMenuItems = null
    this._contextMenuWired = false
    this._onHostContextMenu = this._handleContextMenu.bind(this)
    this._onHostContextKey = this._handleContextKey.bind(this)

    const root = this.attachShadow({ mode: "open" })
    this._adoptStyles(root)
    this._trackBridgedNativeEvents(root)
  }

  /*
   * Remember the native `input`, `focus` and `blur` event that is currently
   * being dispatched inside the shadow root. `emit` uses the record to keep
   * the native event from reaching host listeners a second time when the
   * component re-fires it under the same name (see `emit`).
   */
  _trackBridgedNativeEvents(root) {
    const types = ["input", "focus", "blur"]

    for (let index = 0; index < types.length; index = index + 1) {
      const type = types[index]
      root.addEventListener(type, (event) => {
        this._inflightNativeEvents[type] = event
      }, true)
    }

    return
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
   * the markup -- a string, or the result of the `html` tag from core/html.js,
   * which escapes every interpolated value. Called on the first connect and
   * again when the element is connected after a real removal; a reorder
   * inside the same parent keeps the existing shadow DOM (see
   * `disconnectedCallback`).
   */
  render() {
    const markup = ""
    return markup
  }

  connectedCallback() {
    if (this._disconnectPending === true) {
      this._disconnectPending = false

      if (this.parentNode === this._lastParent) {
        /*
         * Removed and re-inserted under the same parent within one task: a
         * reorder. The shadow DOM, listeners and state are still valid, so
         * nothing is torn down or rebuilt.
         */
        if (this.getAttribute("dock") !== null) {
          registerDockChild(this)
        }
        return
      }

      /* Moved to a different parent: finish the old connection first. */
      this._finishDisconnect()
    }

    const firstRender = this._rendered === false

    if (this._connected === false) {
      const markup = this.render()
      const markupText = markup !== null && markup !== undefined ? String(markup) : ""
      if (markupText.length > 0) {
        this.shadowRoot.innerHTML = markupText
      }
      this.afterRender()
      this._upgradeProperties()
      this._rendered = true
    }

    this._connected = true
    this._lastParent = this.parentNode

    const dockValue = this.getAttribute("dock")
    if (dockValue !== null) {
      registerDockChild(this)
    }

    this.onConnected()

    /* Removed again by the teardown of this connection. */
    this.onTeardown(onLocaleChange((locale) => {
      this._handleLocaleChange(locale)
    }))

    if (firstRender === true) {
      this._replayAttributeChanges()
    }
    return
  }

  /*
   * The locale (or the string table) changed while this component was
   * connected. Skipped for an element that is on its way out: a component
   * that an ancestor's re-render just removed is disconnected but still
   * subscribed until its deferred teardown runs.
   */
  _handleLocaleChange(locale) {
    const live = this.isConnected === true && this._connected === true && this._disconnectPending === false
    if (live === true) {
      this.onLocaleChanged(locale)
    }
    return
  }

  /*
   * Rebuild the shadow DOM from the component's fields and attributes. This
   * is exactly what a removal followed by a re-insert does: the teardown of
   * the current connection, then render(), afterRender() and onConnected().
   * Focus that was inside the component is put back on it.
   */
  renderAgain() {
    if (this._connected === false || this._rendered === false || this.isConnected === false) {
      return
    }

    const hadFocus = this.matches(":focus-within")
    this._finishDisconnect()
    this.connectedCallback()

    if (hadFocus === true) {
      this.focus()
    }
    return
  }

  /*
   * Teardown is deferred by one microtask. Moving an element (insertBefore,
   * append, a keyed re-sort) disconnects and reconnects it synchronously; when
   * it comes back under the same parent the component is left intact instead
   * of being rebuilt, which would discard everything held in its shadow DOM.
   */
  disconnectedCallback() {
    if (this._disconnectPending === true) {
      return
    }
    this._disconnectPending = true

    queueMicrotask(() => {
      if (this._disconnectPending === true) {
        this._disconnectPending = false
        if (this.isConnected === false) {
          this._finishDisconnect()
        }
      }
    })
    return
  }

  _finishDisconnect() {
    unregisterDockChild(this)

    for (let index = 0; index < this._teardown.length; index = index + 1) {
      const dispose = this._teardown[index]
      dispose()
    }
    this._teardown = []

    this._connected = false
    this._lastParent = null
    this.onDisconnected()
    return
  }

  /*
   * Deliver the attribute changes that arrived before the first render a
   * second time, now that the shadow DOM exists. Attributes present in the
   * markup fire `attributeChangedCallback` during upgrade, before
   * `connectedCallback`; a handler that updates shadow nodes can do nothing
   * useful at that point. Only the latest value of each attribute is
   * replayed, and only if the attribute still holds it.
   */
  _replayAttributeChanges() {
    const pending = this._pendingAttributeChanges
    this._pendingAttributeChanges = []

    const latest = {}
    const order = []
    for (let index = 0; index < pending.length; index = index + 1) {
      const change = pending[index]
      if (latest[change.name] === undefined) {
        order.push(change.name)
        latest[change.name] = { oldValue: change.oldValue, newValue: change.newValue }
      } else {
        latest[change.name].newValue = change.newValue
      }
    }

    for (let index = 0; index < order.length; index = index + 1) {
      const name = order[index]
      const change = latest[name]
      if (this.getAttribute(name) === change.newValue) {
        this.onAttributeChanged(name, change.oldValue, change.newValue)
      }
    }

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

    if (this._rendered === false) {
      /*
       * Before the first render the shadow DOM does not exist. The handler
       * still runs so components that only record state keep working, but a
       * failure here is not an error: the change is delivered again by
       * `_replayAttributeChanges` once the component has rendered.
       */
      this._pendingAttributeChanges.push({ name: name, oldValue: oldValue, newValue: newValue })
      try {
        this.onAttributeChanged(name, oldValue, newValue)
      } catch (error) {
        /* Replayed after the first render. */
      }
      return
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

  /*
   * Called when `setLocale` or `registerStrings` changed the locale or the
   * string table. The default renders the component again; a component that
   * can update its text in place overrides this.
   */
  onLocaleChanged(locale) {
    this.renderAgain()
    return
  }

  /* ----- helpers ----- */

  /*
   * Emit a namespaced CustomEvent. All component events are prefixed `mj-`.
   *
   * For events that mirror a standard DOM event (`mj-change`,
   * `mj-input`, `mj-focus`, `mj-blur`), a second event is fired with
   * the bare native name so legacy listeners written against the
   * native form-element API (`el.addEventListener("change", ...)`)
   * keep working when the element is upgraded from a native
   * `<input>` / `<select>` / `<textarea>` to its mj-* equivalent.
   * The bridged event carries the same bubbles/composed flags but is
   * a plain `Event` (no detail) -- consumers that want the rich
   * payload listen for the `mj-*` form. It is not fired when a listener
   * cancelled the `mj-*` event.
   *
   * Native `input`, `focus` and `blur` events are composed, so the one fired
   * by the inner control would reach host listeners as well and they would
   * run twice. When the component emits while that native event is still
   * being dispatched, its propagation is stopped at this point and the
   * bridged event is the only one the outside sees.
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

    if (
      type === "mj-change" ||
      type === "mj-input" ||
      type === "mj-focus" ||
      type === "mj-blur"
    ) {
      const nativeName = type.slice(3)

      const inflight = this._inflightNativeEvents[nativeName]
      if (inflight !== undefined && inflight !== null) {
        if (inflight.eventPhase !== Event.NONE) {
          inflight.stopPropagation()
        }
        this._inflightNativeEvents[nativeName] = null
      }

      /*
       * A cancelled `mj-*` event refused the change (a cancelable mj-change
       * whose listener called preventDefault()), so the native-named event
       * that mirrors it is not fired either.
       */
      if (notCanceled === true) {
        const nativeEvent = new Event(nativeName, {
          bubbles: bubbles,
          cancelable: false,
          composed: composed
        })
        this.dispatchEvent(nativeEvent)
      }
    }

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

  /*
   * Move focus into the component. A host that is itself focusable (it
   * carries a `tabindex`) takes focus as usual; otherwise focus goes to the
   * first focusable control in the shadow DOM, so `element.focus()` and a
   * label activation behave as they do for a native control. Components with
   * a more specific target override this.
   */
  focus(options) {
    let target = null

    if (this.hasAttribute("tabindex") === false && this.shadowRoot !== null) {
      target = this.shadowRoot.querySelector(
        "[data-mj-focus-target], input:not([type='hidden']):not([disabled]), " +
        "textarea:not([disabled]), select:not([disabled]), button:not([disabled]), " +
        "a[href], [tabindex]:not([tabindex='-1'])"
      )
    }

    if (target !== null && typeof target.focus === "function") {
      target.focus(options)
    } else {
      super.focus(options)
    }
    return
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
    /* An inner component (or the page) already handled this request. */
    if (event.defaultPrevented === true) {
      return
    }
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
    if (isContextKey === false || event.defaultPrevented === true) {
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
