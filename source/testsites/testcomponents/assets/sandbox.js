/*
 * sandbox.js
 *
 * Controller of the sandbox on component, chart-type and chart-part pages.
 * Plain JavaScript with no dependency on the component library under test:
 * the library is loaded only inside the preview documents this script
 * builds (see preview.js, inlined into each of them).
 *
 * Panels: the example gallery, the HTML / CSS / JS panes with Run, Reset,
 * "open in new tab" and Copy, the preview with width presets, a drag
 * handle, theme and direction switches, and the inspector with the
 * Controls, Slots, Events and Errors panels.
 *
 * The page data comes from the JSON script element #sandbox-data:
 *   { mode, target, title, examples: [{ key, title, description, html, css,
 *     script, height }], selected, attributes: [{ name, kind, values,
 *     default, description }], slots: [{ name, description, sample }],
 *     presets }
 *
 * It must never contain a closing script tag (it is inlined into HTML).
 */

(function () {
  "use strict"

  const dataElement = document.getElementById("sandbox-data")
  const bootElement = document.getElementById("sandbox-preview-boot")
  const frame = document.getElementById("pg-frame")
  if (dataElement === null || bootElement === null || frame === null) {
    return
  }

  const PAGE = JSON.parse(dataElement.textContent)
  const BOOT = bootElement.textContent
  const CHANNEL = "mj-sandbox"
  /* Never written literally: this file is inlined into a script element. */
  const SCRIPT_OPEN = "<" + "script"
  const SCRIPT_CLOSE = "</" + "script>"
  const COMMENT_OPEN = "<" + "!--"
  const MIN_HEIGHT = 120
  const MAX_HEIGHT = 2400
  const FRAME_BORDER = 2
  const MAX_LOG = 500
  const MIN_WIDTH = 200
  const HANDLE_WIDTH = 12

  const BASE_CSS = [
    ":root[data-theme=light] { color-scheme: light; }",
    ":root[data-theme=dark] { color-scheme: dark; }",
    ":root:not([data-theme]) { color-scheme: light dark; }",
    "body { font-family: var(--mj-font-sans, sans-serif); color: var(--mj-text, #14181f);",
    "  background: var(--mj-bg, #fff); padding: 1rem; margin: 0; }"
  ].join("\n")

  const htmlPane = document.getElementById("pg-code")
  const cssPane = document.getElementById("pg-style")
  const jsPane = document.getElementById("pg-script")
  const exampleFrame = document.getElementById("example-frame")
  const previewBox = document.getElementById("preview-box")
  const previewStage = document.getElementById("preview-stage")
  const sizeReadout = document.getElementById("preview-size")
  const exampleNote = document.getElementById("example-description")
  const statusRegion = document.getElementById("sandbox-status")

  const state = {
    example: null,
    run: 0,
    theme: document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light",
    dir: "ltr",
    width: "full",
    contentHeight: 0,
    exampleHeight: 0,
    exampleFrameExample: null,
    exampleFrameBuilt: false,
    events: [],
    eventFilter: "",
    errors: [],
    detachedSlots: new Map(),
    chartOriginal: null,
    attributeObserver: null,
    observedElement: null
  }


  /* ----- small helpers ------------------------------------------------- */

  function byId(id) {
    const element = document.getElementById(id)
    return element
  }

  function escapeText(value) {
    const text = String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    return text
  }

  function escapeAttribute(value) {
    const text = escapeText(value).replace(/"/g, "&quot;")
    return text
  }

  function announce(message) {
    if (statusRegion !== null) {
      statusRegion.textContent = message
    }
    return
  }

  function exampleByKey(key) {
    let found = PAGE.examples[0]
    for (const example of PAGE.examples) {
      if (example.key === key) {
        found = example
        break
      }
    }
    return found
  }

  function previewDocumentOrNull() {
    let previewDocument = null
    try {
      previewDocument = frame.contentDocument
    } catch (error) {
      previewDocument = null
    }
    return previewDocument
  }

  function firstInstance() {
    const previewDocument = previewDocumentOrNull()
    let element = null
    if (previewDocument !== null && previewDocument.body !== null) {
      element = previewDocument.body.querySelector(PAGE.target)
    }
    return element
  }


  /* The chart the data presets act on: the first <mj-chart> in the preview. */
  function firstChart() {
    const previewDocument = previewDocumentOrNull()
    let chart = null
    if (previewDocument !== null && previewDocument.body !== null) {
      chart = previewDocument.body.querySelector("mj-chart")
    }
    return chart
  }


  /* ----- preview documents --------------------------------------------- */

  function buildPreviewDocument(options) {
    const themeAttribute = options.theme === "os" ? "" : ' data-theme="' + options.theme + '"'
    const config = { run: options.run, script: options.script, retry: options.retry === true }
    const configText = JSON.stringify(config).replace(/</g, "\\u003c")
    const cssText = options.css.replace(/<\/(style)/gi, "<\\/$1")
    const baseTag = options.base !== "" ? '<base href="' + escapeAttribute(options.base) + '">' : ""
    const parts = [
      "<!DOCTYPE html>",
      '<html lang="en"' + themeAttribute + ' dir="' + options.dir + '">',
      "<head>",
      '<meta charset="utf-8">',
      baseTag,
      '<meta name="viewport" content="width=device-width, initial-scale=1">',
      "<title>" + escapeText(options.title) + "</title>",
      '<link rel="stylesheet" href="/static/styles/tokens.css">',
      '<link rel="stylesheet" href="/static/styles/base.css">',
      '<style id="mj-sandbox-base">' + BASE_CSS + "</style>",
      '<style id="mj-sandbox-style">' + cssText + "</style>",
      SCRIPT_OPEN + ' type="application/json" id="mj-sandbox-config">' + configText + SCRIPT_CLOSE,
      SCRIPT_OPEN + ' type="module">' + BOOT + SCRIPT_CLOSE,
      "</head>",
      '<body><template id="mj-sandbox-markup">' + options.html + "</template></body>",
      "</html>"
    ]
    const markup = parts.join("\n")
    return markup
  }

  function currentSource() {
    const source = {
      html: htmlPane.value,
      css: cssPane !== null ? cssPane.value : "",
      script: jsPane !== null ? jsPane.value : ""
    }
    return source
  }

  /*
   * Build a new preview document for the current source. `retry` marks the
   * one rebuild after a transient library load failure (see preview.js).
   */
  function run(retry) {
    state.run += 1
    state.contentHeight = 0
    state.detachedSlots = new Map()
    state.chartOriginal = null
    disconnectAttributeObserver()
    clearErrors()
    if (state.events.length > 0) {
      addLogEntry({ divider: true, type: "Run " + state.run, time: Date.now() })
    }
    const source = currentSource()
    const markup = buildPreviewDocument({
      run: state.run,
      theme: state.theme,
      dir: state.dir,
      base: "",
      title: PAGE.title,
      html: source.html,
      css: source.css,
      script: source.script,
      retry: retry === true
    })
    setControlsAvailable(false)
    frame.setAttribute("srcdoc", markup)
    applyHeight()
    return
  }

  function loadExampleIntoPanes(example) {
    htmlPane.value = example.html
    if (cssPane !== null) {
      cssPane.value = example.css
    }
    if (jsPane !== null) {
      jsPane.value = example.script
    }
    state.exampleHeight = typeof example.height === "number" ? example.height : 0
    return
  }

  function reset() {
    loadExampleIntoPanes(state.example)
    run()
    announce("Example restored")
    return
  }

  function openInNewTab() {
    const source = currentSource()
    const markup = buildPreviewDocument({
      run: 0,
      theme: state.theme,
      dir: state.dir,
      base: location.origin + "/",
      title: PAGE.title + " - " + state.example.title,
      html: source.html,
      css: source.css,
      script: source.script
    })
    const blob = new Blob([markup], { type: "text/html" })
    const url = URL.createObjectURL(blob)
    window.open(url, "_blank")
    setTimeout(() => URL.revokeObjectURL(url), 60000)
    return
  }

  function combinedSnippet() {
    const source = currentSource()
    const pieces = []
    if (source.css.trim() !== "") {
      pieces.push("<style>\n" + source.css.trim() + "\n</style>")
    }
    pieces.push(source.html.trim())
    if (source.script.trim() !== "") {
      pieces.push(SCRIPT_OPEN + ' type="module">\n' + source.script.trim() + "\n" + SCRIPT_CLOSE)
    }
    const snippet = pieces.join("\n\n") + "\n"
    return snippet
  }

  async function copyCode(button) {
    const snippet = combinedSnippet()
    let copied = false
    try {
      await navigator.clipboard.writeText(snippet)
      copied = true
    } catch (error) {
      const scratch = document.createElement("textarea")
      scratch.value = snippet
      scratch.setAttribute("readonly", "")
      scratch.style.position = "fixed"
      scratch.style.opacity = "0"
      document.body.append(scratch)
      scratch.select()
      try {
        copied = document.execCommand("copy") === true
      } catch (copyError) {
        copied = false
      }
      scratch.remove()
    }
    button.setAttribute("data-copied", copied === true ? "true" : "false")
    const label = button.querySelector(".label")
    const original = "Copy"
    if (label !== null) {
      label.textContent = copied === true ? "Copied" : "Copy failed"
      setTimeout(() => {
        label.textContent = original
      }, 1600)
    }
    announce(copied === true ? "Code copied to the clipboard" : "Copy failed")
    return
  }


  /* ----- gallery -------------------------------------------------------- */

  function markSelectedExample(key) {
    for (const chip of document.querySelectorAll("[data-example-chip]")) {
      chip.setAttribute("aria-pressed", chip.getAttribute("data-example-chip") === key ? "true" : "false")
    }
    for (const card of document.querySelectorAll("[data-example-card]")) {
      card.classList.toggle("current", card.getAttribute("data-example-card") === key)
    }
    return
  }

  function selectExample(key, options) {
    const example = exampleByKey(key)
    state.example = example
    loadExampleIntoPanes(example)
    if (exampleNote !== null) {
      exampleNote.innerHTML = example.description
      exampleNote.hidden = example.description.trim() === ""
    }
    markSelectedExample(example.key)
    if (options.updateUrl === true) {
      const url = new URL(location.href)
      url.searchParams.set("example", example.key)
      history.replaceState(null, "", url.toString())
    }
    if (options.run === true) {
      run()
    }
    return
  }


  /* ----- sizing ---------------------------------------------------------- */

  function applyHeight() {
    const minimum = Math.max(MIN_HEIGHT, state.exampleHeight)
    const wanted = Math.max(minimum, state.contentHeight)
    const height = Math.min(MAX_HEIGHT, wanted) + FRAME_BORDER
    frame.style.height = height + "px"
    updateSizeReadout()
    return
  }

  /* The size of the preview's own viewport: the frame without its border. */
  function viewportSize() {
    const size = { width: frame.clientWidth, height: frame.clientHeight }
    return size
  }

  function updateSizeReadout() {
    if (sizeReadout === null) {
      return
    }
    const size = viewportSize()
    sizeReadout.textContent = size.width + " × " + size.height
    return
  }

  /*
   * `width` is the preview viewport width in CSS pixels ("full" = as wide
   * as the stage); the box adds the frame border and the drag handle.
   */
  function setWidth(width) {
    state.width = width
    if (width === "full") {
      previewBox.style.width = "100%"
    } else {
      previewBox.style.width = (width + FRAME_BORDER + HANDLE_WIDTH) + "px"
    }
    for (const button of document.querySelectorAll("[data-preview-width]")) {
      button.setAttribute("aria-pressed", button.getAttribute("data-preview-width") === String(width) ? "true" : "false")
    }
    requestAnimationFrame(updateSizeReadout)
    return
  }

  function wireResizeHandle() {
    const handle = byId("preview-resize-handle")
    if (handle === null) {
      return
    }
    let startX = 0
    let startWidth = 0
    let dragging = false
    const direction = () => (getComputedStyle(previewBox).direction === "rtl" ? -1 : 1)
    handle.addEventListener("pointerdown", (event) => {
      dragging = true
      startX = event.clientX
      startWidth = viewportSize().width
      handle.setPointerCapture(event.pointerId)
      previewBox.classList.add("resizing")
      event.preventDefault()
    })
    handle.addEventListener("pointermove", (event) => {
      if (dragging === false) {
        return
      }
      const width = Math.max(MIN_WIDTH, Math.round(startWidth + (event.clientX - startX) * direction()))
      setWidth(width)
    })
    const stop = (event) => {
      if (dragging === false) {
        return
      }
      dragging = false
      previewBox.classList.remove("resizing")
      if (handle.hasPointerCapture(event.pointerId) === true) {
        handle.releasePointerCapture(event.pointerId)
      }
    }
    handle.addEventListener("pointerup", stop)
    handle.addEventListener("pointercancel", stop)
    handle.addEventListener("keydown", (event) => {
      let delta = 0
      if (event.key === "ArrowRight") {
        delta = 20
      } else if (event.key === "ArrowLeft") {
        delta = -20
      } else {
        return
      }
      event.preventDefault()
      const width = Math.max(MIN_WIDTH, viewportSize().width + delta)
      setWidth(width)
    })
    return
  }


  /* ----- theme and direction ------------------------------------------- */

  function applyTheme(theme) {
    state.theme = theme
    for (const target of [frame, exampleFrame]) {
      if (target === null) {
        continue
      }
      let root = null
      try {
        root = target.contentDocument !== null ? target.contentDocument.documentElement : null
      } catch (error) {
        root = null
      }
      if (root !== null) {
        if (theme === "os") {
          root.removeAttribute("data-theme")
        } else {
          root.setAttribute("data-theme", theme)
        }
      }
    }
    for (const button of document.querySelectorAll("[data-preview-theme]")) {
      button.setAttribute("aria-pressed", button.getAttribute("data-preview-theme") === theme ? "true" : "false")
    }
    return
  }

  function applyDirection(dir) {
    state.dir = dir
    for (const target of [frame, exampleFrame]) {
      if (target === null) {
        continue
      }
      let root = null
      try {
        root = target.contentDocument !== null ? target.contentDocument.documentElement : null
      } catch (error) {
        root = null
      }
      if (root !== null) {
        root.setAttribute("dir", dir)
      }
    }
    for (const button of document.querySelectorAll("[data-preview-dir]")) {
      button.setAttribute("aria-pressed", button.getAttribute("data-preview-dir") === dir ? "true" : "false")
    }
    return
  }


  /* ----- HTML pane sync -------------------------------------------------- */

  /*
   * Find the first opening tag of `tag` in the source (outside comments)
   * and the span of every attribute in it.
   */
  function findOpeningTag(source, tag) {
    const lower = source.toLowerCase()
    let from = 0
    let found = null
    while (found === null) {
      const at = lower.indexOf("<" + tag, from)
      if (at === -1) {
        break
      }
      const after = lower.charAt(at + 1 + tag.length)
      const commentStart = lower.lastIndexOf(COMMENT_OPEN, at)
      const insideComment = commentStart !== -1 && lower.indexOf("-->", commentStart) > at
      if (/[\s>/]/.test(after) === false || insideComment === true) {
        from = at + 1
        continue
      }
      found = parseOpeningTag(source, at, tag)
      if (found === null) {
        break
      }
    }
    return found
  }

  function parseOpeningTag(source, start, tag) {
    let index = start + 1 + tag.length
    const attributes = []
    let result = null
    while (index < source.length) {
      while (index < source.length && /\s/.test(source.charAt(index)) === true) {
        index += 1
      }
      const character = source.charAt(index)
      if (character === ">") {
        result = { start: start, close: index, attributes: attributes }
        break
      }
      if (character === "/" && source.charAt(index + 1) === ">") {
        result = { start: start, close: index, attributes: attributes }
        break
      }
      if (character === "/") {
        index += 1
        continue
      }
      const nameStart = index
      while (index < source.length && /[\s=>/]/.test(source.charAt(index)) === false) {
        index += 1
      }
      const name = source.slice(nameStart, index).toLowerCase()
      let end = index
      let look = index
      while (look < source.length && /\s/.test(source.charAt(look)) === true) {
        look += 1
      }
      if (source.charAt(look) === "=") {
        look += 1
        while (look < source.length && /\s/.test(source.charAt(look)) === true) {
          look += 1
        }
        const quote = source.charAt(look)
        if (quote === '"' || quote === "'") {
          const closing = source.indexOf(quote, look + 1)
          if (closing === -1) {
            return null
          }
          end = closing + 1
        } else {
          end = look
          while (end < source.length && /[\s>]/.test(source.charAt(end)) === false) {
            end += 1
          }
        }
        index = end
      }
      attributes.push({ name: name, start: nameStart, end: end })
    }
    return result
  }

  function formatAttribute(name, value) {
    let text = name
    if (value !== "") {
      const amp = value.replace(/&/g, "&amp;")
      if (value.indexOf('"') === -1) {
        text = name + '="' + amp + '"'
      } else if (value.indexOf("'") === -1) {
        text = name + "='" + amp + "'"
      } else {
        text = name + '="' + amp.replace(/"/g, "&quot;") + '"'
      }
    }
    return text
  }

  function syncHtmlPane(name, value) {
    const source = htmlPane.value
    const tag = findOpeningTag(source, PAGE.target)
    if (tag === null) {
      announce("The HTML pane has no <" + PAGE.target + "> tag to update")
      return false
    }
    let existing = null
    for (const attribute of tag.attributes) {
      if (attribute.name === name.toLowerCase()) {
        existing = attribute
        break
      }
    }
    let updated = source
    if (existing !== null) {
      if (value === null) {
        let removeFrom = existing.start
        while (removeFrom > 0 && /\s/.test(source.charAt(removeFrom - 1)) === true) {
          removeFrom -= 1
        }
        updated = source.slice(0, removeFrom) + source.slice(existing.end)
      } else {
        updated = source.slice(0, existing.start) + formatAttribute(name, value) + source.slice(existing.end)
      }
    } else if (value !== null) {
      let insertAt = tag.close
      while (insertAt > tag.start && /\s/.test(source.charAt(insertAt - 1)) === true) {
        insertAt -= 1
      }
      updated = source.slice(0, insertAt) + " " + formatAttribute(name, value) + source.slice(insertAt)
    }
    htmlPane.value = updated
    return true
  }


  /* ----- controls panel --------------------------------------------------- */

  const controls = new Map()

  /* Parses CSS colours for the colour controls (fillStyle normalises them). */
  const colourContext = document.createElement("canvas").getContext("2d")

  /*
   * Parse a CSS colour into the #rrggbb the native picker can show and its
   * alpha (0..1). Returns null for an empty or unparsable value (a var(),
   * a typo).
   */
  function parseColour(value) {
    let parsed = null
    if (colourContext === null || typeof value !== "string" || value.trim() === "") {
      return parsed
    }
    /* An invalid value leaves fillStyle unchanged: two sentinels tell it apart. */
    colourContext.fillStyle = "#010203"
    colourContext.fillStyle = value
    const first = String(colourContext.fillStyle)
    colourContext.fillStyle = "#040506"
    colourContext.fillStyle = value
    const second = String(colourContext.fillStyle)
    if (first !== second) {
      return parsed
    }
    if (/^#[0-9a-f]{6}$/i.test(first) === true) {
      parsed = { hex: first.toLowerCase(), alpha: 1 }
    } else {
      const match = /^rgba?\(\s*(\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\s*\)$/.exec(first)
      if (match !== null) {
        const hex = "#" + [match[1], match[2], match[3]].map((part) => Number(part).toString(16).padStart(2, "0")).join("")
        const alpha = match[4] !== undefined ? Number(match[4]) : 1
        parsed = { hex: hex, alpha: alpha }
      }
    }
    return parsed
  }

  function alphaHex(alpha) {
    const text = Math.round(Math.min(1, Math.max(0, alpha)) * 255).toString(16).padStart(2, "0")
    return text
  }

  /*
   * Show a colour value on the swatch. The native picker holds only
   * #rrggbb, so a translucent or unparsable value is marked on the row
   * (the text field next to it shows the exact value).
   */
  function showColour(entry, value) {
    const parsed = parseColour(value)
    entry.input.value = parsed !== null ? parsed.hex : "#000000"
    entry.row.classList.toggle("color-unset", value === null)
    const approximate = value !== null && (parsed === null || parsed.alpha < 1)
    entry.row.classList.toggle("color-approximate", approximate)
    entry.input.title = approximate === true ? "The picker shows the colour without its transparency" : ""
    return
  }

  /* A colour picked on the swatch keeps the alpha of the value it replaces. */
  function onColourSwatchInput(entry) {
    let value = entry.input.value
    const previous = parseColour(entry.text.value)
    if (previous !== null && previous.alpha < 1) {
      value = value + alphaHex(previous.alpha)
    }
    entry.text.value = value
    showColour(entry, value)
    applyAttribute(entry, value)
    return
  }

  /* Any CSS colour can be typed: #rrggbbaa, rgb(), hsl(), a name, a var(). */
  function onColourTextInput(entry) {
    const text = entry.text.value.trim()
    const value = text === "" ? null : text
    showColour(entry, value)
    applyAttribute(entry, value)
    return
  }

  function controlId(name) {
    const id = "control-" + name.replace(/[^a-zA-Z0-9_-]/g, "_")
    return id
  }

  function readControlValue(entry) {
    const attribute = entry.attribute
    const input = entry.input
    let value = null
    if (attribute.kind === "boolean") {
      const inverted = attribute.default === "true"
      if (inverted === true) {
        value = input.checked === true ? null : "false"
      } else {
        value = input.checked === true ? "" : null
      }
    } else if (attribute.kind === "enum") {
      value = input.value === "" ? null : input.value
    } else if (attribute.kind === "color") {
      value = entry.text.value.trim() === "" ? null : entry.text.value.trim()
    } else if (attribute.kind === "json") {
      const text = input.value.trim()
      if (text === "") {
        value = null
      } else {
        value = JSON.stringify(JSON.parse(text))
      }
    } else {
      value = input.value === "" ? null : input.value
    }
    return value
  }

  function writeControlValue(entry, current) {
    const attribute = entry.attribute
    const input = entry.input
    entry.row.classList.toggle("is-set", current !== null)
    if (attribute.kind === "boolean") {
      if (attribute.default === "true") {
        input.checked = current === null || current !== "false"
      } else {
        input.checked = current !== null && current !== "false"
      }
    } else if (attribute.kind === "enum") {
      let known = current === null
      for (const option of input.options) {
        if (option.value === current) {
          known = true
        }
      }
      if (known === false) {
        const option = document.createElement("option")
        option.value = current
        option.textContent = current + " (not listed)"
        input.append(option)
      }
      input.value = current === null ? "" : current
    } else if (attribute.kind === "color") {
      if (document.activeElement !== entry.text) {
        entry.text.value = current === null ? "" : current
      }
      showColour(entry, current)
    } else if (attribute.kind === "json") {
      if (document.activeElement !== input) {
        let pretty = current === null ? "" : current
        try {
          if (current !== null) {
            pretty = JSON.stringify(JSON.parse(current), null, 2)
          }
        } catch (error) {
          pretty = current
        }
        input.value = pretty
      }
      input.removeAttribute("aria-invalid")
    } else if (document.activeElement !== input) {
      input.value = current === null ? "" : current
    }
    return
  }

  function applyAttribute(entry, value) {
    const element = firstInstance()
    if (element === null) {
      return
    }
    const name = entry.attribute.name
    if (value === null) {
      element.removeAttribute(name)
    } else {
      element.setAttribute(name, value)
    }
    syncHtmlPane(name, value)
    entry.row.classList.toggle("is-set", value !== null)
    return
  }

  function onControlInput(entry) {
    let value = null
    try {
      value = readControlValue(entry)
    } catch (error) {
      entry.input.setAttribute("aria-invalid", "true")
      announce("Not valid JSON: " + error.message)
      return
    }
    entry.input.removeAttribute("aria-invalid")
    applyAttribute(entry, value)
    return
  }

  function buildControl(attribute) {
    const row = document.createElement("div")
    row.className = "control-row kind-" + attribute.kind
    row.setAttribute("data-testid", "control-row-" + attribute.name)
    const id = controlId(attribute.name)

    const label = document.createElement("label")
    label.className = "control-label"
    label.setAttribute("for", id)
    const nameCode = document.createElement("code")
    nameCode.textContent = attribute.name
    const kind = document.createElement("span")
    kind.className = "control-kind"
    kind.textContent = attribute.kind
    label.append(nameCode, kind)

    let input = null
    if (attribute.kind === "boolean") {
      input = document.createElement("input")
      input.type = "checkbox"
    } else if (attribute.kind === "enum") {
      input = document.createElement("select")
      const unset = document.createElement("option")
      unset.value = ""
      unset.textContent = "(not set)"
      input.append(unset)
      for (const value of attribute.values) {
        const option = document.createElement("option")
        option.value = value
        option.textContent = value === attribute.default ? value + " (default)" : value
        input.append(option)
      }
    } else if (attribute.kind === "json") {
      input = document.createElement("textarea")
      input.rows = 4
      input.spellcheck = false
      input.placeholder = "JSON; applied on blur or Ctrl+Enter"
    } else {
      input = document.createElement("input")
      input.type = attribute.kind === "number" ? "number" : (attribute.kind === "color" ? "color" : "text")
      if (attribute.kind === "string" && attribute.values.length > 0) {
        const list = document.createElement("datalist")
        list.id = id + "-values"
        for (const value of attribute.values) {
          const option = document.createElement("option")
          option.value = value
          list.append(option)
        }
        row.append(list)
        input.setAttribute("list", list.id)
      }
      if (attribute.default !== null && attribute.kind !== "color") {
        input.placeholder = attribute.default
      }
    }
    input.id = id
    input.className = "control-input"
    input.setAttribute("data-testid", id)
    input.setAttribute("data-attribute", attribute.name)

    const clear = document.createElement("button")
    clear.type = "button"
    clear.className = "control-clear"
    clear.textContent = "×"
    clear.title = "Remove the attribute"
    clear.setAttribute("aria-label", "Remove " + attribute.name)
    clear.setAttribute("data-testid", id + "-clear")

    const entry = { attribute: attribute, input: input, row: row, text: null }

    /* A colour has a swatch and a text field with the exact value (alpha, names). */
    if (attribute.kind === "color") {
      const text = document.createElement("input")
      text.type = "text"
      text.id = id + "-text"
      text.className = "control-input control-colour-text"
      text.spellcheck = false
      text.placeholder = attribute.default !== null ? attribute.default : "#rrggbb, #rrggbbaa, rgb(), a name"
      text.setAttribute("aria-label", attribute.name + " value")
      text.setAttribute("data-testid", id + "-text")
      text.setAttribute("data-attribute", attribute.name)
      input.setAttribute("aria-label", attribute.name + " colour picker")
      entry.text = text
    }

    if (attribute.kind === "json") {
      input.addEventListener("change", () => onControlInput(entry))
      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && (event.ctrlKey === true || event.metaKey === true)) {
          event.preventDefault()
          onControlInput(entry)
        }
      })
    } else if (attribute.kind === "color") {
      input.addEventListener("input", () => onColourSwatchInput(entry))
      input.addEventListener("change", () => onColourSwatchInput(entry))
      entry.text.addEventListener("input", () => onColourTextInput(entry))
    } else if (attribute.kind === "boolean" || attribute.kind === "enum") {
      input.addEventListener("input", () => onControlInput(entry))
      input.addEventListener("change", () => onControlInput(entry))
    } else {
      input.addEventListener("input", () => onControlInput(entry))
    }
    clear.addEventListener("click", () => {
      applyAttribute(entry, null)
      writeControlValue(entry, null)
    })

    const field = document.createElement("div")
    field.className = "control-field"
    if (entry.text !== null) {
      field.append(input, entry.text, clear)
    } else {
      field.append(input, clear)
    }

    const help = document.createElement("div")
    help.className = "control-help"
    help.innerHTML = attribute.descriptionHtml !== undefined ? attribute.descriptionHtml : escapeText(attribute.description)

    row.append(label, field, help)
    controls.set(attribute.name, entry)
    return row
  }

  function buildControlsPanel() {
    const container = byId("controls-list")
    if (container === null) {
      return
    }
    for (const attribute of PAGE.attributes) {
      container.append(buildControl(attribute))
    }
    return
  }

  function setControlsAvailable(available) {
    const panel = byId("panel-controls")
    if (panel !== null) {
      panel.classList.toggle("no-target", available === false)
    }
    for (const entry of controls.values()) {
      entry.input.disabled = available === false
      if (entry.text !== null) {
        entry.text.disabled = available === false
      }
    }
    return
  }

  function refreshControls() {
    const element = firstInstance()
    const missing = byId("controls-missing")
    if (missing !== null) {
      missing.hidden = element !== null
    }
    setControlsAvailable(element !== null)
    if (element === null) {
      return
    }
    for (const entry of controls.values()) {
      writeControlValue(entry, element.getAttribute(entry.attribute.name))
    }
    observeAttributes(element)
    return
  }

  function disconnectAttributeObserver() {
    if (state.attributeObserver !== null) {
      state.attributeObserver.disconnect()
      state.attributeObserver = null
    }
    state.observedElement = null
    return
  }

  /* Keep the controls in step when the component changes its own attributes. */
  function observeAttributes(element) {
    if (state.observedElement === element) {
      return
    }
    disconnectAttributeObserver()
    const view = element.ownerDocument.defaultView
    if (view === null) {
      return
    }
    state.attributeObserver = new view.MutationObserver((records) => {
      for (const record of records) {
        const entry = controls.get(record.attributeName)
        if (entry !== undefined) {
          writeControlValue(entry, element.getAttribute(record.attributeName))
        }
      }
    })
    state.attributeObserver.observe(element, { attributes: true })
    state.observedElement = element
    return
  }


  /* ----- chart data presets --------------------------------------------- */

  function readChartData(chart) {
    let data = null
    if (chart.data !== null && chart.data !== undefined) {
      data = chart.data
    } else {
      const inline = chart.querySelector(':scope > script[type="application/json"]')
      if (inline !== null) {
        try {
          data = JSON.parse(inline.textContent)
        } catch (error) {
          data = null
        }
      }
    }
    return data
  }

  function presetSupport(data) {
    const support = { categories: false, series: false, numeric: false }
    if (data === null || typeof data !== "object") {
      return support
    }
    support.categories = Array.isArray(data.categories) === true
    if (Array.isArray(data.series) === true && data.series.length > 0) {
      let allValues = true
      let allNumeric = true
      for (const series of data.series) {
        if (series === null || typeof series !== "object" || Array.isArray(series.values) === false) {
          allValues = false
          allNumeric = false
          break
        }
        for (const value of series.values) {
          if (value !== null && typeof value !== "number") {
            allNumeric = false
          }
        }
      }
      support.series = allValues
      support.numeric = allValues === true && allNumeric === true
    }
    return support
  }

  function waveValue(index, seriesIndex, base) {
    const wave = 1 + 0.5 * Math.sin(index / 25 + seriesIndex) + 0.15 * Math.sin(index * 1.7 + seriesIndex)
    const value = Math.round(base * wave * 100) / 100
    return value
  }

  function presetData(name, data) {
    const copy = JSON.parse(JSON.stringify(data))
    const support = presetSupport(copy)
    const count = 1000
    if (name === "empty") {
      if (support.categories === true) {
        copy.categories = []
      }
      if (support.series === true) {
        for (const series of copy.series) {
          series.values = []
        }
      }
    } else if (name === "single") {
      if (support.categories === true) {
        copy.categories = copy.categories.slice(0, 1)
      }
      if (support.series === true) {
        for (const series of copy.series) {
          series.values = series.values.slice(0, 1)
        }
      }
    } else if (name === "negative") {
      if (support.numeric === true) {
        for (const series of copy.series) {
          series.values = series.values.map((value, index) => {
            let result = value
            if (typeof value === "number") {
              result = index % 2 === 0 ? -Math.abs(value) : Math.abs(value)
            }
            return result
          })
        }
      }
    } else if (name === "large") {
      if (support.categories === true) {
        const labels = []
        for (let index = 0; index < count; index += 1) {
          labels.push("P" + (index + 1))
        }
        copy.categories = labels
      }
      if (support.series === true) {
        copy.series.forEach((series, seriesIndex) => {
          const original = series.values
          const numbers = original.filter((value) => typeof value === "number")
          let base = 10
          if (numbers.length > 0) {
            base = numbers.reduce((sum, value) => sum + Math.abs(value), 0) / numbers.length
            if (base === 0) {
              base = 10
            }
          }
          const values = []
          for (let index = 0; index < count; index += 1) {
            if (support.numeric === true || original.length === 0) {
              values.push(waveValue(index, seriesIndex, base))
            } else {
              values.push(original[index % original.length])
            }
          }
          series.values = values
        })
      }
    }
    return copy
  }

  function refreshPresets() {
    const container = byId("chart-presets")
    if (container === null) {
      return
    }
    const chart = firstChart()
    const data = chart !== null ? readChartData(chart) : null
    const support = presetSupport(data)
    const usable = support.categories === true || support.series === true
    for (const button of container.querySelectorAll("[data-preset]")) {
      const preset = button.getAttribute("data-preset")
      let enabled = usable
      if (preset === "negative") {
        enabled = support.numeric === true
      }
      if (preset === "original") {
        enabled = usable === true || state.chartOriginal !== null
      }
      button.disabled = enabled === false
    }
    const note = byId("chart-presets-note")
    if (note !== null) {
      note.hidden = usable === true
    }
    return
  }

  function applyPreset(name) {
    const chart = firstChart()
    if (chart === null) {
      return
    }
    if (state.chartOriginal === null) {
      state.chartOriginal = { property: chart.data, parsed: readChartData(chart) }
    }
    if (name === "original") {
      chart.data = state.chartOriginal.property !== undefined ? state.chartOriginal.property : null
    } else if (state.chartOriginal.parsed !== null) {
      chart.data = presetData(name, state.chartOriginal.parsed)
    }
    for (const button of document.querySelectorAll("[data-preset]")) {
      button.setAttribute("aria-pressed", button.getAttribute("data-preset") === name ? "true" : "false")
    }
    announce("Data preset: " + name)
    return
  }


  /* ----- slot inspector ------------------------------------------------- */

  /* The documented named slots; content for any other slot name is default content. */
  const NAMED_SLOTS = new Set(PAGE.slots.map((slot) => slot.name).filter((name) => name !== ""))

  /*
   * The light-DOM nodes of the first instance that are content for a slot.
   * Default-slot content is every child that does not go to a documented
   * named slot: a child without a slot attribute, and also one whose slot
   * the component assigned itself (mj-breadcrumb moves its crumbs to
   * slot="mj-crumb-N", for example).
   */
  function slotNodes(element, name) {
    const nodes = []
    for (const child of Array.from(element.childNodes)) {
      if (name === "") {
        if (child.nodeType === Node.TEXT_NODE && child.textContent.trim() !== "") {
          nodes.push(child)
        } else if (child.nodeType === Node.ELEMENT_NODE) {
          const skipped = ["script", "template", "style"].indexOf(child.localName) !== -1
          const named = child.hasAttribute("slot") === true && NAMED_SLOTS.has(child.getAttribute("slot")) === true
          if (skipped === false && named === false) {
            nodes.push(child)
          }
        }
      } else if (child.nodeType === Node.ELEMENT_NODE && child.getAttribute("slot") === name) {
        nodes.push(child)
      }
    }
    return nodes
  }

  function sampleNodes(element, slot) {
    const ownerDocument = element.ownerDocument
    const template = ownerDocument.createElement("template")
    let sample = slot.sample
    if (sample === "") {
      sample = slot.name === "" ? "Sample content" : escapeText(slot.name)
    }
    template.innerHTML = sample
    const fragment = ownerDocument.importNode(template.content, true)
    const nodes = []
    for (const node of Array.from(fragment.childNodes)) {
      if (node.nodeType === Node.TEXT_NODE) {
        if (node.textContent.trim() === "") {
          continue
        }
        if (slot.name !== "") {
          const wrapper = ownerDocument.createElement("span")
          wrapper.setAttribute("slot", slot.name)
          wrapper.append(node)
          nodes.push(wrapper)
        } else {
          nodes.push(node)
        }
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        if (slot.name !== "" && node.hasAttribute("slot") === false) {
          node.setAttribute("slot", slot.name)
        }
        nodes.push(node)
      }
    }
    return nodes
  }

  function toggleSlot(slot, on) {
    const element = firstInstance()
    if (element === null) {
      return
    }
    if (on === false) {
      const nodes = slotNodes(element, slot.name)
      for (const node of nodes) {
        node.remove()
      }
      state.detachedSlots.set(slot.name, nodes)
    } else {
      let nodes = state.detachedSlots.get(slot.name)
      if (nodes === undefined || nodes.length === 0) {
        nodes = sampleNodes(element, slot)
      }
      state.detachedSlots.delete(slot.name)
      for (const node of nodes) {
        element.append(node)
      }
    }
    refreshSlots()
    return
  }

  function refreshSlots() {
    const element = firstInstance()
    for (const toggle of document.querySelectorAll("[data-slot-toggle]")) {
      const name = toggle.getAttribute("data-slot-toggle")
      toggle.disabled = element === null
      toggle.checked = element !== null && slotNodes(element, name).length > 0
    }
    return
  }

  function wireSlots() {
    for (const toggle of document.querySelectorAll("[data-slot-toggle]")) {
      const name = toggle.getAttribute("data-slot-toggle")
      let slot = null
      for (const candidate of PAGE.slots) {
        if (candidate.name === name) {
          slot = candidate
        }
      }
      if (slot === null) {
        continue
      }
      toggle.addEventListener("change", () => toggleSlot(slot, toggle.checked === true))
    }
    return
  }


  /* ----- event log -------------------------------------------------------- */

  function formatTime(milliseconds) {
    const date = new Date(milliseconds)
    const pad = (value, size) => String(value).padStart(size, "0")
    const text = pad(date.getHours(), 2) + ":" + pad(date.getMinutes(), 2) + ":" +
      pad(date.getSeconds(), 2) + "." + pad(date.getMilliseconds(), 3)
    return text
  }

  function entryMatchesFilter(entry) {
    const filter = state.eventFilter
    let matches = true
    if (filter !== "" && entry.divider !== true) {
      const haystack = (entry.type + " " + entry.target + " " + entry.detail).toLowerCase()
      matches = haystack.indexOf(filter) !== -1
    }
    return matches
  }

  function renderLogEntry(entry) {
    const item = document.createElement("li")
    if (entry.divider === true) {
      item.className = "log-divider"
      item.textContent = entry.type
      return item
    }
    item.className = entry.log === true ? "log-entry is-log" : "log-entry"
    item.setAttribute("data-testid", "event-log-entry")
    item.setAttribute("data-event", entry.type)
    const time = document.createElement("time")
    time.textContent = formatTime(entry.time)
    const name = document.createElement("code")
    name.className = "log-type"
    name.textContent = entry.type
    const target = document.createElement("span")
    target.className = "log-target"
    target.textContent = entry.target
    item.append(time, name, target)
    if (entry.detail !== "") {
      const detail = document.createElement("code")
      detail.className = "log-detail"
      detail.textContent = entry.detail
      item.append(detail)
    }
    return item
  }

  function updateEventCount() {
    let count = 0
    for (const entry of state.events) {
      if (entry.divider !== true) {
        count += 1
      }
    }
    for (const badge of document.querySelectorAll("[data-event-count]")) {
      badge.textContent = String(count)
    }
    const label = byId("event-log-count")
    if (label !== null) {
      label.textContent = count === 1 ? "1 event" : count + " events"
    }
    return
  }

  function addLogEntry(entry) {
    state.events.push(entry)
    while (state.events.length > MAX_LOG) {
      state.events.shift()
    }
    const list = byId("event-log")
    if (list !== null) {
      const item = renderLogEntry(entry)
      item.hidden = entryMatchesFilter(entry) === false
      list.prepend(item)
      while (list.children.length > MAX_LOG) {
        list.lastElementChild.remove()
      }
    }
    updateEventCount()
    return
  }

  function clearEvents() {
    state.events = []
    const list = byId("event-log")
    if (list !== null) {
      list.replaceChildren()
    }
    updateEventCount()
    return
  }

  function filterEvents(text) {
    state.eventFilter = text.trim().toLowerCase()
    const list = byId("event-log")
    if (list === null) {
      return
    }
    const items = Array.from(list.children)
    const entries = state.events.slice().reverse()
    items.forEach((item, index) => {
      const entry = entries[index]
      if (entry !== undefined) {
        item.hidden = entryMatchesFilter(entry) === false
      }
    })
    return
  }


  /* ----- error panel ------------------------------------------------------ */

  function updateErrorCount() {
    const count = state.errors.length
    for (const badge of document.querySelectorAll("[data-error-count]")) {
      badge.textContent = String(count)
      badge.classList.toggle("has-errors", count > 0)
    }
    const label = byId("error-count")
    if (label !== null) {
      label.textContent = count === 1 ? "1 error" : count + " errors"
    }
    const empty = byId("error-empty")
    if (empty !== null) {
      empty.hidden = count > 0
    }
    return
  }

  function addError(error) {
    state.errors.push(error)
    const list = byId("error-list")
    if (list !== null) {
      const item = document.createElement("li")
      item.className = "error-entry"
      item.setAttribute("data-testid", "error-entry")
      const message = document.createElement("div")
      message.className = "error-message"
      message.textContent = error.message
      item.append(message)
      if (error.source !== "" && error.source !== undefined) {
        const where = document.createElement("div")
        where.className = "error-source"
        where.textContent = error.source + (error.line > 0 ? ":" + error.line + ":" + error.column : "")
        item.append(where)
      }
      if (error.stack !== "" && error.stack !== undefined) {
        const details = document.createElement("details")
        const summary = document.createElement("summary")
        summary.textContent = "Stack"
        const stack = document.createElement("pre")
        stack.textContent = error.stack
        details.append(summary, stack)
        item.append(details)
      }
      list.append(item)
    }
    updateErrorCount()
    return
  }

  function clearErrors() {
    state.errors = []
    const list = byId("error-list")
    if (list !== null) {
      list.replaceChildren()
    }
    updateErrorCount()
    return
  }


  /* ----- the Examples tab view ------------------------------------------ */

  function showInExampleFrame(key, retry) {
    if (exampleFrame === null) {
      return
    }
    const example = exampleByKey(key)
    state.exampleFrameExample = example
    state.exampleFrameBuilt = true
    const markup = buildPreviewDocument({
      run: -1,
      theme: state.theme,
      dir: state.dir,
      base: "",
      title: PAGE.title + " - " + example.title,
      html: example.html,
      css: example.css,
      script: example.script,
      retry: retry === true
    })
    const minimum = Math.max(240, typeof example.height === "number" ? example.height : 0)
    exampleFrame.style.height = (minimum + FRAME_BORDER) + "px"
    exampleFrame.setAttribute("srcdoc", markup)
    for (const card of document.querySelectorAll("[data-example-card]")) {
      card.classList.toggle("viewing", card.getAttribute("data-example-card") === example.key)
    }
    return
  }

  function sizeExampleFrame(height) {
    if (exampleFrame === null || state.exampleFrameExample === null) {
      return
    }
    const example = state.exampleFrameExample
    const minimum = Math.max(240, typeof example.height === "number" ? example.height : 0)
    const wanted = Math.min(MAX_HEIGHT, Math.max(minimum, height))
    exampleFrame.style.height = (wanted + FRAME_BORDER) + "px"
    return
  }


  /* ----- messages from the preview ------------------------------------- */

  window.addEventListener("message", (event) => {
    const message = event.data
    if (message === null || typeof message !== "object" || message.channel !== CHANNEL) {
      return
    }
    if (exampleFrame !== null && event.source === exampleFrame.contentWindow) {
      if (message.kind === "size") {
        sizeExampleFrame(message.payload.height)
      } else if (message.kind === "retry" && state.exampleFrameExample !== null) {
        showInExampleFrame(state.exampleFrameExample.key, true)
      }
      return
    }
    if (event.source !== frame.contentWindow || message.run !== state.run) {
      return
    }
    const payload = message.payload
    if (message.kind === "size") {
      state.contentHeight = payload.height
      applyHeight()
    } else if (message.kind === "event") {
      addLogEntry({
        type: payload.type,
        target: payload.target,
        detail: payload.detail,
        time: payload.time,
        log: payload.log === true
      })
    } else if (message.kind === "error") {
      addError(payload)
    } else if (message.kind === "retry") {
      /* The library failed to load transiently: build the preview again, once. */
      addLogEntry({
        type: "library load retried",
        target: "sandbox",
        detail: String(payload.message),
        time: Date.now(),
        log: true
      })
      run(true)
    } else if (message.kind === "ready") {
      refreshControls()
      refreshSlots()
      refreshPresets()
      frame.setAttribute("data-ready-run", String(state.run))
    }
    return
  })


  /* ----- wiring ----------------------------------------------------------- */

  function on(id, type, handler) {
    const element = byId(id)
    if (element !== null) {
      element.addEventListener(type, handler)
    }
    return element
  }

  on("pg-run", "click", () => run())
  on("pg-reset", "click", () => reset())
  on("pg-open", "click", () => openInNewTab())
  const copyButton = on("pg-copy", "click", () => copyCode(copyButton))
  on("event-log-clear", "click", () => clearEvents())
  on("error-clear", "click", () => clearErrors())
  on("event-log-filter", "input", (event) => filterEvents(event.target.value))

  for (const textarea of [htmlPane, cssPane, jsPane]) {
    if (textarea === null) {
      continue
    }
    textarea.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && (event.ctrlKey === true || event.metaKey === true)) {
        event.preventDefault()
        run()
      }
    })
  }

  for (const chip of document.querySelectorAll("[data-example-chip]")) {
    chip.addEventListener("click", () => {
      selectExample(chip.getAttribute("data-example-chip"), { run: true, updateUrl: true })
    })
  }
  for (const button of document.querySelectorAll("[data-example-open]")) {
    button.addEventListener("click", () => {
      selectExample(button.getAttribute("data-example-open"), { run: true, updateUrl: true })
      const playTab = byId("tab-play")
      if (playTab !== null) {
        playTab.click()
        playTab.focus()
      }
    })
  }
  for (const button of document.querySelectorAll("[data-example-view]")) {
    button.addEventListener("click", () => showInExampleFrame(button.getAttribute("data-example-view")))
  }
  for (const button of document.querySelectorAll("[data-preview-width]")) {
    button.addEventListener("click", () => {
      const value = button.getAttribute("data-preview-width")
      setWidth(value === "full" ? "full" : Number(value))
    })
  }
  for (const button of document.querySelectorAll("[data-preview-theme]")) {
    button.addEventListener("click", () => applyTheme(button.getAttribute("data-preview-theme")))
  }
  for (const button of document.querySelectorAll("[data-preview-dir]")) {
    button.addEventListener("click", () => applyDirection(button.getAttribute("data-preview-dir")))
  }
  for (const button of document.querySelectorAll("[data-preset]")) {
    button.addEventListener("click", () => applyPreset(button.getAttribute("data-preset")))
  }

  /* The Examples tab builds its own preview only when it is first shown. */
  const exampleTab = byId("tab-example")
  if (exampleTab !== null) {
    exampleTab.addEventListener("tabselect", () => {
      if (state.exampleFrameBuilt === false) {
        showInExampleFrame(state.example.key)
      }
    })
  }

  /* The header theme toggle carries the preview along. */
  document.addEventListener("site-theme-change", (event) => {
    applyTheme(event.detail.theme)
  })

  window.addEventListener("resize", () => requestAnimationFrame(updateSizeReadout))

  buildControlsPanel()
  wireSlots()
  wireResizeHandle()
  setWidth("full")
  applyTheme(state.theme)
  applyDirection(state.dir)
  updateEventCount()
  updateErrorCount()
  selectExample(PAGE.selected, { run: true, updateUrl: false })

  /* For tests and debugging. */
  window.mjSandboxPage = {
    state: state,
    run: run,
    selectExample: selectExample,
    applyPreset: applyPreset,
    firstInstance: firstInstance,
    firstChart: firstChart
  }
})()
