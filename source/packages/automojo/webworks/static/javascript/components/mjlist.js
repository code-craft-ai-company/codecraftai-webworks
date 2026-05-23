/*
 * mjlist.js
 *
 * <mj-list> -- semantic list primitive rendering ordered (<ol>), unordered
 * (<ul>), or description (<dl>) lists with token-driven spacing, optional
 * dividers, nested level support, and item-click events.
 */

import { MjElement } from "../core/mjelement.js";

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

li {
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

:host([density="compact"]) ul,
:host([density="compact"]) ol { gap: var(--mj-list-gap-compact, 2px); }

:host([density="spacious"]) ul,
:host([density="spacious"]) ol { gap: var(--mj-list-gap-spacious, 12px); }

:host([nested]) { padding-inline-start: var(--mj-list-indent, 20px); }

hr.divider {
  border: none;
  border-top: 1px solid var(--mj-list-divider-color, var(--mj-border));
  margin: 0;
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

export class MjList extends MjElement {
  static tagName = "mj-list";
  static styles = STYLES;
  static watched = ["type", "marker", "density", "nested", "dividers", "start", "reversed"];

  constructor() {
    super()
    this._items = []
  }

  render() {
    const type = this.getAttribute("type") || "unordered"
    if (type === "description") {
      return `<dl part="list" role="list"><slot></slot></dl>`
    }
    if (type === "ordered") {
      return `<ol part="list"><slot></slot></ol>`
    }
    return `<ul part="list"><slot></slot></ul>`
  }

  afterRender() {
    this._listEl = this.$("ul") || this.$("ol") || this.$("dl")
    this._syncMarker()
    this._syncListAttrs()

    if (this._items.length > 0) {
      this._renderItems()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._listEl === undefined || this._listEl === null) {
      return
    }
    if (name === "type") {
      const markup = this.render()
      this.shadowRoot.innerHTML = markup
      this._listEl = this.$("ul") || this.$("ol") || this.$("dl")
    }
    if (name === "marker") {
      this._syncMarker()
    }
    if (name === "start" || name === "reversed") {
      this._syncListAttrs()
    }
    return
  }

  _syncMarker() {
    const marker = this.getAttribute("marker") || "bullet"
    this._listEl.setAttribute("data-marker", marker)
    if (marker === "none") {
      this._listEl.setAttribute("role", "list")
    } else {
      this._listEl.removeAttribute("role")
    }
    return
  }

  _syncListAttrs() {
    const type = this.getAttribute("type") || "unordered"
    if (type !== "ordered") {
      return
    }
    const ol = this.$("ol")
    if (ol === null) {
      return
    }
    const start = this.getAttribute("start")
    if (start !== null && start.length > 0) {
      ol.setAttribute("start", start)
    }
    const reversed = this.hasAttribute("reversed")
    if (reversed === true) {
      ol.setAttribute("reversed", "")
    } else {
      ol.removeAttribute("reversed")
    }
    return
  }

  _renderItems() {
    const type = this.getAttribute("type") || "unordered"
    this._listEl.innerHTML = ""

    if (type === "description") {
      this._renderDescriptionItems()
      return
    }

    const dividers = this.hasAttribute("dividers")

    for (let idx = 0; idx < this._items.length; idx = idx + 1) {
      const item = this._items[idx]
      const li = this._buildListItem(item, idx)
      this._listEl.appendChild(li)

      if (dividers === true && idx < this._items.length - 1) {
        const hr = document.createElement("hr")
        hr.className = "divider"
        hr.setAttribute("part", "divider")
        hr.setAttribute("aria-hidden", "true")
        this._listEl.appendChild(hr)
      }
    }
    return
  }

  _buildListItem(item, idx) {
    const li = document.createElement("li")
    li.setAttribute("part", "item")

    if (item.href !== undefined && item.href !== null) {
      const a = document.createElement("a")
      a.href = item.href
      a.textContent = item.label
      this.listen(a, "click", () => {
        this.emit("mj-item-click", { index: idx, label: item.label, href: item.href })
      })
      li.appendChild(a)
    } else if (item.action !== undefined) {
      const btn = document.createElement("button")
      btn.textContent = item.label
      this.listen(btn, "click", () => {
        this.emit("mj-item-click", { index: idx, label: item.label })
      })
      li.appendChild(btn)
    } else {
      li.textContent = item.label
    }

    if (item.children !== undefined && item.children !== null && item.children.length > 0) {
      const nested = document.createElement("mj-list")
      nested.setAttribute("nested", "")
      nested.setAttribute("type", this.getAttribute("type") || "unordered")
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

      if (item.description !== undefined) {
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
