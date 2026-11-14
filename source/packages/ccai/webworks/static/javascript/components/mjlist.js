/*
 * mjlist.js
 *
 * <mj-list> -- semantic list primitive rendering ordered (<ol>), unordered
 * (<ul>), or description (<dl>) lists with token-driven spacing, optional
 * dividers, nested level support, and item-click events.
 *
 * Items come from light-DOM <li> children (default slot) or from the `items`
 * property: `{ label, href?, action?, icon?, description?, children? }`.
 * `href` values pass through `safeUrl`, so `javascript:` URLs are inert.
 */

import { MjElement } from "../core/mjelement.js";
import { safeUrl } from "../core/html.js";

const STYLES = `
:host {
  display: block;
  font: inherit;
  color: var(--mj-text);
}

ul, ol {
  list-style: none;
  margin: 0;
  padding-inline-start: 0;
  display: flex;
  flex-direction: column;
  gap: var(--mj-list-gap, 6px);
}
ul[data-marker="bullet"]  { list-style: disc; padding-inline-start: var(--mj-list-indent, 20px); }
ul[data-marker="disc"]    { list-style: disc; padding-inline-start: var(--mj-list-indent, 20px); }
ul[data-marker="circle"]  { list-style: circle; padding-inline-start: var(--mj-list-indent, 20px); }
ul[data-marker="square"]  { list-style: square; padding-inline-start: var(--mj-list-indent, 20px); }

ol[data-marker="decimal"] { list-style: decimal; padding-inline-start: var(--mj-list-indent, 20px); }
ol[data-marker="alpha"]   { list-style: lower-alpha; padding-inline-start: var(--mj-list-indent, 20px); }
ol[data-marker="roman"]   { list-style: lower-roman; padding-inline-start: var(--mj-list-indent, 20px); }

/* role="list" is added when marker="none" for Safari */
ul[role="list"], ol[role="list"] { list-style: none; padding-inline-start: 0; }

li, ::slotted(li) {
  padding: 0;
  line-height: var(--mj-line-height);
}
li a, li button {
  color: var(--mj-accent);
  text-decoration: none;
  cursor: pointer;
  background: none;
  border: none;
  font: inherit;
  padding: 0;
}
li a:hover, li button:hover { text-decoration: underline; }
li a:focus-visible, li button:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.item-icon { margin-inline-end: var(--mj-space-2); }

:host([density="compact"]) ul,
:host([density="compact"]) ol { gap: var(--mj-list-gap-compact, 2px); }

:host([density="spacious"]) ul,
:host([density="spacious"]) ol { gap: var(--mj-list-gap-spacious, 12px); }

:host([nested]) { padding-inline-start: var(--mj-list-indent, 20px); }

/* Dividers are borders on the items, so the list holds nothing but <li>. */
:host([dividers]) li + li,
:host([dividers]) ::slotted(li:not(:first-child)) {
  border-block-start: 1px solid var(--mj-list-divider-color, var(--mj-border));
  padding-block-start: var(--mj-list-gap, 6px);
}
:host([dividers][density="compact"]) li + li,
:host([dividers][density="compact"]) ::slotted(li:not(:first-child)) {
  padding-block-start: var(--mj-list-gap-compact, 2px);
}
:host([dividers][density="spacious"]) li + li,
:host([dividers][density="spacious"]) ::slotted(li:not(:first-child)) {
  padding-block-start: var(--mj-list-gap-spacious, 12px);
}

dl {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--mj-list-gap, 6px);
}
dt {
  font-weight: var(--mj-list-term-weight, 600);
  color: var(--mj-text);
}
dd {
  margin-inline-start: var(--mj-list-indent, 20px);
  color: var(--mj-text-muted);
}
`;

/* Attributes a nested list takes over from the list that contains it. */
const INHERITED_ATTRIBUTES = ["marker", "density", "dividers"];

export class MjList extends MjElement {
  static tagName = "mj-list";
  static styles = STYLES;
  static watched = ["type", "marker", "density", "nested", "dividers", "start", "reversed"];

  constructor() {
    super()
    this._items = []
    this._listEl = null
  }

  render() {
    const type = this.getAttribute("type") || "unordered"
    let markup = `<ul part="list"><slot></slot></ul>`
    if (type === "description") {
      markup = `<dl part="list"><slot></slot></dl>`
    } else if (type === "ordered") {
      markup = `<ol part="list"><slot></slot></ol>`
    }
    return markup
  }

  afterRender() {
    /* One delegated listener serves every link / button item. */
    this.listen(this.shadowRoot, "click", this._onClick.bind(this))
    this._bindList()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._listEl === undefined || this._listEl === null) {
      return
    }
    if (name === "type") {
      const wantedTag = this._tagForType()
      if (this._listEl.localName !== wantedTag) {
        /* A different list element is needed; rebuild it and its content. */
        this.shadowRoot.innerHTML = this.render()
        this._bindList()
      }
    }
    if (name === "marker") {
      this._syncMarker()
    }
    if (name === "start" || name === "reversed") {
      this._syncListAttrs()
    }
    if (name === "marker" || name === "density" || name === "dividers") {
      this._syncNestedLists()
    }
    return
  }

  _tagForType() {
    const type = this.getAttribute("type") || "unordered"
    let tag = "ul"
    if (type === "description") {
      tag = "dl"
    } else if (type === "ordered") {
      tag = "ol"
    }
    return tag
  }

  /* Pick up the list element of the current shadow tree and fill it. */
  _bindList() {
    this._listEl = this.$("ul") || this.$("ol") || this.$("dl")
    this._syncMarker()
    this._syncListAttrs()

    if (this._items.length > 0) {
      this._renderItems()
    }
    return
  }

  _syncMarker() {
    const tag = this._listEl.localName
    if (tag === "dl") {
      /* A description list keeps its native semantics and has no marker. */
      this._listEl.removeAttribute("data-marker")
      this._listEl.removeAttribute("role")
      return
    }

    const fallback = tag === "ol" ? "decimal" : "bullet"
    const marker = this.getAttribute("marker") || fallback
    this._listEl.setAttribute("data-marker", marker)
    if (marker === "none") {
      this._listEl.setAttribute("role", "list")
    } else {
      this._listEl.removeAttribute("role")
    }
    return
  }

  _syncListAttrs() {
    const ol = this.$("ol")
    if (ol === null) {
      return
    }
    const start = this.getAttribute("start")
    if (start !== null && start.length > 0) {
      ol.setAttribute("start", start)
    } else {
      ol.removeAttribute("start")
    }
    const reversed = this.hasAttribute("reversed")
    if (reversed === true) {
      ol.setAttribute("reversed", "")
    } else {
      ol.removeAttribute("reversed")
    }
    return
  }

  /* Copy marker, density and dividers onto a nested list. */
  _applyInheritedAttributes(nested) {
    for (let i = 0; i < INHERITED_ATTRIBUTES.length; i = i + 1) {
      const name = INHERITED_ATTRIBUTES[i]
      const value = this.getAttribute(name)
      if (value !== null) {
        nested.setAttribute(name, value)
      } else {
        nested.removeAttribute(name)
      }
    }
    return
  }

  _syncNestedLists() {
    const nestedLists = this._listEl.querySelectorAll("mj-list")
    for (let i = 0; i < nestedLists.length; i = i + 1) {
      this._applyInheritedAttributes(nestedLists[i])
    }
    return
  }

  _renderItems() {
    const type = this.getAttribute("type") || "unordered"
    this._listEl.replaceChildren()

    if (type === "description") {
      this._renderDescriptionItems()
    } else {
      for (let idx = 0; idx < this._items.length; idx = idx + 1) {
        const item = this._items[idx]
        const li = this._buildListItem(item, idx)
        this._listEl.appendChild(li)
      }
    }

    if (this._items.length === 0) {
      /* No data items: light-DOM <li> children show through the slot again. */
      this._listEl.appendChild(document.createElement("slot"))
    }
    return
  }

  _buildListItem(item, idx) {
    const li = document.createElement("li")
    li.setAttribute("part", "item")
    const label = item.label !== undefined && item.label !== null ? String(item.label) : ""

    if (item.icon !== undefined && item.icon !== null && item.icon !== "") {
      const icon = document.createElement("span")
      icon.className = "item-icon"
      icon.setAttribute("part", "item-icon")
      icon.setAttribute("aria-hidden", "true")
      icon.textContent = String(item.icon)
      li.appendChild(icon)
    }

    if (item.href !== undefined && item.href !== null) {
      const a = document.createElement("a")
      a.setAttribute("href", safeUrl(item.href))
      a.setAttribute("data-item-index", String(idx))
      a.textContent = label
      li.appendChild(a)
    } else if (item.action !== undefined) {
      const btn = document.createElement("button")
      btn.type = "button"
      btn.setAttribute("data-item-index", String(idx))
      btn.textContent = label
      li.appendChild(btn)
    } else {
      li.appendChild(document.createTextNode(label))
    }

    if (item.children !== undefined && item.children !== null && item.children.length > 0) {
      const nested = document.createElement("mj-list")
      nested.setAttribute("nested", "")
      nested.setAttribute("type", this.getAttribute("type") || "unordered")
      this._applyInheritedAttributes(nested)
      li.appendChild(nested)
      nested.items = item.children
    }

    return li
  }

  _renderDescriptionItems() {
    for (let idx = 0; idx < this._items.length; idx = idx + 1) {
      const item = this._items[idx]
      const dt = document.createElement("dt")
      dt.setAttribute("part", "term")
      dt.textContent = item.label
      this._listEl.appendChild(dt)

      if (item.description !== undefined && item.description !== null) {
        const descriptions = Array.isArray(item.description) ? item.description : [item.description]
        for (let di = 0; di < descriptions.length; di = di + 1) {
          const dd = document.createElement("dd")
          dd.setAttribute("part", "definition")
          dd.textContent = descriptions[di]
          this._listEl.appendChild(dd)
        }
      }
    }
    return
  }

  _onClick(event) {
    const target = event.target
    if (!(target instanceof Element)) {
      return
    }
    const control = target.closest("[data-item-index]")
    if (control === null) {
      return
    }
    const idx = parseInt(control.getAttribute("data-item-index"), 10)
    const item = this._items[idx]
    if (item === undefined) {
      return
    }

    const detail = { index: idx, label: item.label }
    if (control.localName === "a") {
      detail.href = item.href
    }
    this.emit("mj-item-click", detail)
    return
  }

  /* ----- scriptable API ----- */

  get items() {
    return this._items
  }

  set items(value) {
    this._items = Array.isArray(value) === true ? value : []
    if (this._listEl !== undefined && this._listEl !== null) {
      this._renderItems()
    }
    return
  }
}
