/*
 * preview.js
 *
 * Bootstrap of the sandbox preview document. The sandbox page inlines this
 * file as the one module script in the head of every preview document it
 * builds (the live preview, the Examples tab view and the "open in new tab"
 * view). It runs after the document is parsed and:
 *
 *   1. installs the instrumentation: uncaught errors, unhandled rejections,
 *      every mj-* event (and change / input) and the content height are
 *      reported to the sandbox page with postMessage;
 *   2. moves the example markup out of its <template> into the body with
 *      its executable script elements held back;
 *   3. imports the component library and waits until every mj-* tag in the
 *      body that the library registers is defined, so every element is
 *      upgraded (data-only child tags such as <mj-option> are never
 *      registered and are not waited for);
 *   4. runs the held scripts in document order, then the JS pane as a
 *      module script.
 *
 * It also keeps links and form submissions from navigating the preview:
 * an srcdoc document resolves every URL against the sandbox page, so even
 * href="#top" would load the catalog page into the preview.
 *
 * It must not depend on the component library and must never contain a
 * closing script tag (it is inlined into HTML).
 */

const CHANNEL = "mj-sandbox"
const LIBRARY_URL = "/static/javascript/index.js"
/* Imported by index.js, so importing it again only reads its exports. */
const CHART_LIBRARY_URL = "/static/javascript/charts/index.js"
const DEFINE_TIMEOUT_MS = 5000
const DETAIL_LIMIT = 300

const configElement = document.getElementById("mj-sandbox-config")
const config = JSON.parse(configElement.textContent)
const hostWindow = window.parent !== window ? window.parent : null

/* Executable script types (the JavaScript MIME types and "module"). */
const EXECUTABLE_TYPE = /^(|module|(text|application)\/(x-)?(java|ecma)script(1\.[0-5])?|text\/(jscript|livescript))$/i
const HELD_TYPE = "text/x-mj-held"


/* ----- reporting --------------------------------------------------------- */

function post(kind, payload) {
  if (hostWindow === null) {
    return
  }
  const message = { channel: CHANNEL, run: config.run, kind: kind, payload: payload }
  try {
    hostWindow.postMessage(message, "*")
  } catch (error) {
    /* A payload that cannot be cloned is dropped; payloads are plain data. */
  }
  return
}

function isNode(value) {
  const result = value !== null && typeof value === "object" &&
    typeof value.nodeType === "number" && typeof value.nodeName === "string"
  return result
}

function nodeLabel(node) {
  let label = node.nodeName.toLowerCase()
  if (node.nodeType === 1) {
    label = "<" + node.localName
    if (node.id !== "") {
      label += "#" + node.id
    }
    label += ">"
  }
  return label
}

/* A bounded, cycle-safe plain copy of an event detail, for display. */
function toPlain(value, depth, seen) {
  let result = value
  const type = typeof value
  if (value === null || value === undefined) {
    result = value === undefined ? "undefined" : null
  } else if (type === "string") {
    result = value.length > 120 ? value.slice(0, 117) + "..." : value
  } else if (type === "number" || type === "boolean") {
    result = value
  } else if (type === "bigint") {
    result = value.toString() + "n"
  } else if (type === "function") {
    result = "[function " + (value.name !== "" ? value.name : "anonymous") + "]"
  } else if (type === "symbol") {
    result = value.toString()
  } else if (isNode(value) === true) {
    result = nodeLabel(value)
  } else if (value instanceof Event) {
    result = "[" + value.type + " event]"
  } else if (value instanceof Date) {
    result = value.toISOString()
  } else if (value instanceof Error) {
    result = value.name + ": " + value.message
  } else if (seen.has(value) === true) {
    result = "[circular]"
  } else if (depth >= 3) {
    result = Array.isArray(value) === true ? "[" + value.length + " items]" : "{...}"
  } else {
    seen.add(value)
    if (Array.isArray(value) === true) {
      result = []
      const shown = Math.min(value.length, 10)
      for (let index = 0; index < shown; index += 1) {
        result.push(toPlain(value[index], depth + 1, seen))
      }
      if (value.length > shown) {
        result.push("... " + (value.length - shown) + " more")
      }
    } else if (value instanceof Map || value instanceof Set) {
      result = toPlain(Array.from(value), depth, seen)
    } else {
      result = {}
      const keys = Object.keys(value)
      const shown = Math.min(keys.length, 12)
      for (let index = 0; index < shown; index += 1) {
        const key = keys[index]
        let entry = null
        try {
          entry = toPlain(value[key], depth + 1, seen)
        } catch (error) {
          entry = "[unreadable]"
        }
        result[key] = entry
      }
      if (keys.length > shown) {
        result["..."] = (keys.length - shown) + " more"
      }
    }
  }
  return result
}

function summarize(value) {
  let text = ""
  if (value === undefined || value === null) {
    return text
  }
  try {
    text = JSON.stringify(toPlain(value, 0, new WeakSet()))
  } catch (error) {
    text = String(value)
  }
  if (text === undefined) {
    text = String(value)
  }
  if (text.length > DETAIL_LIMIT) {
    text = text.slice(0, DETAIL_LIMIT - 3) + "..."
  }
  return text
}

function targetLabel(target) {
  let label = String(target)
  if (target === window) {
    label = "window"
  } else if (target === document) {
    label = "document"
  } else if (isNode(target) === true) {
    label = nodeLabel(target).replace(/^<|>$/g, "")
    const root = typeof target.getRootNode === "function" ? target.getRootNode() : null
    if (root !== null && root.host !== undefined && root.host !== null) {
      label += " in " + root.host.localName
    }
  }
  return label
}

function recordEvent(event, target) {
  post("event", {
    type: event.type,
    target: targetLabel(target),
    detail: summarize(event.detail),
    trusted: event.isTrusted === true,
    time: Date.now()
  })
  return
}

function shouldRecord(type) {
  const result = type.startsWith("mj-") === true || type === "change" || type === "input"
  return result
}

/* Every script-dispatched event goes through dispatchEvent. */
const nativeDispatch = EventTarget.prototype.dispatchEvent
EventTarget.prototype.dispatchEvent = function (event) {
  if (event !== null && typeof event === "object" && typeof event.type === "string") {
    if (shouldRecord(event.type) === true) {
      recordEvent(event, this)
    }
  }
  const result = nativeDispatch.call(this, event)
  return result
}

/* Native input / change from controls in the light DOM. */
for (const type of ["input", "change"]) {
  window.addEventListener(type, (event) => {
    if (event.isTrusted === true) {
      recordEvent(event, event.target)
    }
  }, true)
}

function shortSource(url) {
  let text = typeof url === "string" ? url : ""
  if (text.startsWith(location.origin) === true) {
    text = text.slice(location.origin.length)
  }
  if (text === "about:srcdoc" || text.startsWith("blob:") === true) {
    text = "preview"
  }
  return text
}

window.addEventListener("error", (event) => {
  const error = event.error
  const stack = error !== null && error !== undefined && error.stack !== undefined ? String(error.stack) : ""
  post("error", {
    kind: "error",
    message: event.message !== "" ? event.message : String(error),
    source: shortSource(event.filename),
    line: event.lineno,
    column: event.colno,
    stack: stack
  })
})

window.addEventListener("unhandledrejection", (event) => {
  const reason = event.reason
  let message = ""
  let stack = ""
  if (reason instanceof Error) {
    message = reason.name + ": " + reason.message
    stack = reason.stack !== undefined ? String(reason.stack) : ""
  } else {
    message = summarize(reason)
  }
  post("error", { kind: "rejection", message: "Unhandled rejection: " + message, source: "", line: 0, column: 0, stack: stack })
})


/* ----- content height ---------------------------------------------------- */

let lastHeight = -1
let measureScheduled = false
const OVERLAY_MARGIN = 16
const FULL_HEIGHT_SLACK = 24
const MAX_OVERLAY_CANDIDATES = 600

/* How much taller a box would be if it and its scrolling parts showed everything. */
function overflowExtra(element) {
  let extra = Math.max(0, element.scrollHeight - element.clientHeight)
  const descendants = element.querySelectorAll("*")
  const shown = Math.min(descendants.length, 200)
  for (let index = 0; index < shown; index += 1) {
    const descendant = descendants[index]
    const overflow = getComputedStyle(descendant).overflowY
    if (overflow === "auto" || overflow === "scroll") {
      extra = Math.max(extra, descendant.scrollHeight - descendant.clientHeight)
    }
  }
  return extra
}

/* The height each open overlay needed so far; it never shrinks while open. */
const overlayNeeds = new WeakMap()

/*
 * Content outside the flow -- an open modal dialog or popover in the top
 * layer, a fixed panel -- does not give the body any height. Find the
 * height such boxes need (in the light DOM and in open shadow roots) so
 * the preview can grow to show them.
 *
 * A box placed against the viewport (centred, or near the bottom) needs
 * its own height, what it hides by scrolling, and its gaps; any other box
 * needs room down to its bottom edge. A box about as tall as the viewport
 * that hides nothing (a backdrop, a full-height drawer, a 100vh panel) is
 * ignored: it grows with the preview and would never fit. What a box
 * needed is remembered while it stays open, so a dialog that fits once it
 * has room does not shrink the preview again and oscillate.
 */
function outOfFlowHeight() {
  let height = 0
  const viewportHeight = window.innerHeight
  const roots = [document]
  const candidates = []
  while (roots.length > 0) {
    const root = roots.pop()
    for (const element of root.querySelectorAll("dialog[open], [popover]")) {
      candidates.push(element)
    }
    for (const element of root.querySelectorAll("*")) {
      if (element.shadowRoot !== null && element.shadowRoot !== undefined) {
        roots.push(element.shadowRoot)
        for (const child of element.shadowRoot.children) {
          candidates.push(child)
        }
      }
      if (element.localName.startsWith("mj-") === true) {
        candidates.push(element)
      }
    }
  }
  /* Bounded: a page with thousands of elements checks the first ones only. */
  const checked = candidates.slice(0, MAX_OVERLAY_CANDIDATES)
  for (const element of checked) {
    const needed = overlayNeed(element, viewportHeight)
    if (needed === null) {
      /* Closed, hidden or parked off-screen: forget what it needed while open. */
      overlayNeeds.delete(element)
      continue
    }
    height = Math.max(height, needed)
  }
  return height
}

/*
 * The height one candidate needs, or null when it is not an open overlay
 * that shows: a closed dialog or popover, an element that is not fixed, a
 * box with no height, a box hidden with visibility (a closed drawer panel
 * that stays in place), or a fixed box lying wholly outside the viewport
 * (a panel parked off-screen with a transform until it slides in).
 */
function overlayNeed(element, viewportHeight) {
  let style = null
  let outside = false
  if (element.localName === "dialog" && element.open === true) {
    outside = true
  } else if (element.hasAttribute("popover") === true) {
    outside = element.matches(":popover-open") === true
  } else {
    style = getComputedStyle(element)
    outside = style.position === "fixed"
  }
  if (outside === false) {
    return null
  }
  if (style === null) {
    style = getComputedStyle(element)
  }
  if (style.visibility !== "visible") {
    return null
  }
  const rect = element.getBoundingClientRect()
  if (rect.height <= 0) {
    return null
  }
  if (rect.top >= viewportHeight || rect.bottom <= 0) {
    return null
  }
  const remembered = overlayNeeds.has(element) === true ? overlayNeeds.get(element) : 0
  /* A box held smaller than its content (max-height: calc(100vh - ...)). */
  const extra = overflowExtra(element)
  /*
   * About as tall as the viewport (100vh, inset: 0) grows with it; a box
   * taller than the viewport has a size of its own and needs room.
   */
  const nearlyFull = rect.height > viewportHeight - FULL_HEIGHT_SLACK && rect.height <= viewportHeight + 1
  if (nearlyFull === true && extra <= 0) {
    return remembered
  }
  let top = rect.top
  let bottom = rect.bottom
  /*
   * A box that reaches past the bottom edge only because a transform moves
   * it (a bottom sheet sliding in) is measured where its layout puts it:
   * growing the preview would move it down with the edge and never show it.
   */
  if (bottom > viewportHeight && style.transform !== "none" && element.offsetParent === null) {
    const layoutBottom = element.offsetTop + element.offsetHeight
    if (layoutBottom <= viewportHeight) {
      top = element.offsetTop
      bottom = layoutBottom
    }
  }
  const boxHeight = bottom - top
  const topGap = Math.max(0, top)
  const bottomGap = viewportHeight - bottom
  const centred = Math.abs(top - bottomGap) <= 2
  const nearBottom = bottomGap >= 0 && bottomGap <= OVERLAY_MARGIN * 2
  let needed = 0
  if (centred === true) {
    needed = boxHeight + extra + Math.max(topGap + Math.max(0, bottomGap), OVERLAY_MARGIN * 2)
  } else if (nearBottom === true) {
    needed = boxHeight + extra + bottomGap + OVERLAY_MARGIN
  } else {
    needed = bottom + window.scrollY + extra + OVERLAY_MARGIN
  }
  needed = Math.max(needed, remembered)
  overlayNeeds.set(element, needed)
  return needed
}

function measure() {
  measureScheduled = false
  const body = document.body
  if (body === null) {
    return
  }
  const style = getComputedStyle(body)
  const box = body.getBoundingClientRect()
  const margins = parseFloat(style.marginTop) + parseFloat(style.marginBottom)
  const flowHeight = Math.max(body.scrollHeight, box.height) + margins
  const height = Math.ceil(Math.max(flowHeight, outOfFlowHeight()))
  if (Math.abs(height - lastHeight) >= 1) {
    lastHeight = height
    post("size", { height: height })
  }
  return
}

function scheduleMeasure() {
  if (measureScheduled === true) {
    return
  }
  measureScheduled = true
  requestAnimationFrame(measure)
  return
}

function watchSize() {
  const resizeObserver = new ResizeObserver(scheduleMeasure)
  resizeObserver.observe(document.documentElement)
  resizeObserver.observe(document.body)
  const mutationObserver = new MutationObserver(scheduleMeasure)
  mutationObserver.observe(document.documentElement, {
    subtree: true, childList: true, attributes: true, characterData: true
  })
  for (const type of ["click", "keyup", "transitionend", "animationend", "toggle", "load", "close"]) {
    window.addEventListener(type, scheduleMeasure, true)
  }
  window.addEventListener("resize", scheduleMeasure)
  scheduleMeasure()
  return
}


/* ----- the sandbox helper global ---------------------------------------- */

let resolveReady = null
const readyPromise = new Promise((resolve) => {
  resolveReady = resolve
})

window.mjSandbox = {
  ready: false,
  whenReady: readyPromise,
  /* performance.now() when the library had loaded and when the held scripts were released. */
  timing: { library: null, scripts: null },
  log(label, detail) {
    post("event", {
      type: String(label),
      target: "mjSandbox.log",
      detail: summarize(detail),
      trusted: false,
      time: Date.now(),
      log: true
    })
    return
  },
  _scriptDone(run) {
    if (run === config.run) {
      finish()
    }
    return
  }
}

function finish() {
  if (window.mjSandbox.ready === true) {
    return
  }
  window.mjSandbox.ready = true
  const tags = usedTags()
  const unregistered = []
  for (const tag of tags) {
    if (customElements.get(tag) === undefined) {
      unregistered.push(tag)
    }
  }
  post("ready", { tags: tags, unregistered: unregistered })
  scheduleMeasure()
  resolveReady(true)
  return
}

/* Every mj-* tag name used in the document. */
function usedTags() {
  const tags = new Set()
  for (const element of document.querySelectorAll("*")) {
    if (element.localName.startsWith("mj-") === true) {
      tags.add(element.localName)
    }
  }
  const result = Array.from(tags)
  return result
}


/* ----- the component library -------------------------------------------- */

/*
 * The tag names the library registers, from the `registeredTags` export of
 * index.js and the `registeredChartTags` export of the chart library; null
 * when the library did not load or does not export them.
 */
let libraryTags = null

function addLibraryTags(list) {
  if (Array.isArray(list) === false) {
    return
  }
  if (libraryTags === null) {
    libraryTags = new Set()
  }
  for (const tag of list) {
    if (typeof tag === "string") {
      libraryTags.add(tag)
    }
  }
  return
}

function reportLibraryFailure(error) {
  post("error", {
    kind: "error",
    message: "The component library failed to load: " + String(error),
    source: LIBRARY_URL, line: 0, column: 0,
    stack: error !== null && error !== undefined && error.stack !== undefined ? String(error.stack) : ""
  })
  return
}

/*
 * Whether a failed library import may be retried in a new preview document.
 * A fetch failure ("Failed to fetch dynamically imported module", a
 * TypeError) can be transient: under heavy load the browser occasionally
 * fails one of the ~260 module requests although the server answered it.
 * The failure stays in this document's module map, so only a new document
 * can try again; the sandbox page builds one once per run. A SyntaxError or
 * a missing export is a real defect and is reported at once.
 */
function retriable(error) {
  const result = error instanceof TypeError && config.retry !== true && hostWindow !== null
  return result
}

/*
 * Import the library. Resolves "loaded", "failed" (reported in the Errors
 * panel) or "retrying" (the sandbox page replaces this document).
 */
async function loadLibrary() {
  let library = null
  let outcome = "failed"
  try {
    library = await import(LIBRARY_URL)
  } catch (error) {
    if (retriable(error) === true) {
      outcome = "retrying"
      post("retry", { message: String(error) })
    } else {
      reportLibraryFailure(error)
    }
  }
  if (library !== null) {
    outcome = "loaded"
    addLibraryTags(library.registeredTags)
    try {
      const charts = await import(CHART_LIBRARY_URL)
      addLibraryTags(charts.registeredChartTags)
    } catch (error) {
      reportLibraryFailure(error)
    }
  }
  return outcome
}

/*
 * The tags in the document that the library registers but that are not
 * defined yet. A tag the library does not register -- a data-only child
 * such as <mj-option>, <mj-radio> or <mj-tree-item>, read by its parent --
 * is never defined, so waiting for it would only hold the scripts back
 * until the timeout. Without the library's tag list every undefined mj-*
 * tag is waited for.
 */
function pendingLibraryTags() {
  const pending = []
  for (const tag of usedTags()) {
    const registered = libraryTags === null || libraryTags.has(tag) === true
    if (registered === true && customElements.get(tag) === undefined) {
      pending.push(tag)
    }
  }
  return pending
}


/* ----- navigation guard ------------------------------------------------- */

/*
 * The preview is an srcdoc document whose base URL is the sandbox page's,
 * so a link -- even href="#section" -- or a form submission would load the
 * catalog page into the preview (or, with target="_top", replace the
 * sandbox page). Such navigations are cancelled and logged in the Events
 * panel. A link to a fragment of the preview itself goes to that fragment,
 * as it would on a real page (:target, hashchange and scrolling work).
 *
 * The click and submit guards run when the event reaches the window, so an
 * example or component that handles the event (and calls preventDefault)
 * decides first. The Navigation API, where the browser has it, catches the
 * navigations the guards cannot see (a listener that stopped propagation,
 * location.assign() in a script).
 */

function logBlocked(label, detail) {
  window.mjSandbox.log(label, detail)
  return
}

function withoutFragment(url) {
  const hashAt = url.indexOf("#")
  const result = hashAt === -1 ? url : url.slice(0, hashAt)
  return result
}

/*
 * The fragment a URL points at when it addresses this document: written as
 * "#name", or resolved against the base URL (the sandbox page) to it.
 * Returns null for any other URL.
 */
function ownFragment(rawHref, resolvedHref) {
  let fragment = null
  const raw = rawHref.trim()
  if (raw.startsWith("#") === true) {
    fragment = raw.slice(1)
  } else if (resolvedHref.indexOf("#") !== -1) {
    const sameAsBase = withoutFragment(resolvedHref) === withoutFragment(document.baseURI)
    const sameAsDocument = withoutFragment(resolvedHref) === withoutFragment(location.href)
    if (sameAsBase === true || sameAsDocument === true) {
      fragment = resolvedHref.slice(resolvedHref.indexOf("#") + 1)
    }
  }
  return fragment
}

/* Go to a fragment of the preview, the way following "#fragment" would. */
function goToFragment(fragment) {
  let moved = false
  try {
    location.hash = fragment
    moved = true
  } catch (error) {
    moved = false
  }
  if (moved === false) {
    let name = fragment
    try {
      name = decodeURIComponent(fragment)
    } catch (error) {
      name = fragment
    }
    let target = document.getElementById(name)
    if (target === null) {
      target = document.querySelector('a[name="' + CSS.escape(name) + '"]')
    }
    if (target !== null) {
      target.scrollIntoView()
    }
  }
  return
}

/* The link a click activates: the innermost <a href> / <area href> on its path. */
function activatedLink(event) {
  let link = null
  const path = typeof event.composedPath === "function" ? event.composedPath() : []
  for (const node of path) {
    if (node === null || node.nodeType !== 1) {
      continue
    }
    const name = node.localName
    if ((name === "a" || name === "area") && node.hasAttribute("href") === true) {
      link = node
      break
    }
  }
  return link
}

function onLinkClick(event) {
  if (event.defaultPrevented === true) {
    return
  }
  const link = activatedLink(event)
  if (link === null || link.hasAttribute("download") === true) {
    return
  }
  const rawHref = link.getAttribute("href")
  /* An SVG <a> has an animated href; resolve the attribute ourselves. */
  let resolved = rawHref
  try {
    resolved = new URL(rawHref, document.baseURI).href
  } catch (error) {
    resolved = rawHref
  }
  /* A javascript: URL runs in the preview and does not leave it. */
  if (resolved.trim().toLowerCase().startsWith("javascript:") === true) {
    return
  }
  const target = (link.getAttribute("target") || "").trim().toLowerCase()
  const fragment = ownFragment(rawHref, resolved)
  event.preventDefault()
  if (fragment !== null && (target === "" || target === "_self")) {
    goToFragment(fragment)
  } else {
    logBlocked("link navigation blocked", { href: rawHref, target: target })
  }
  return
}

function onFormSubmit(event) {
  if (event.defaultPrevented === true) {
    return
  }
  const form = event.target
  const submitter = event.submitter !== undefined && event.submitter !== null ? event.submitter : null
  let method = form.getAttribute("method") || "get"
  if (submitter !== null && submitter.hasAttribute("formmethod") === true) {
    method = submitter.getAttribute("formmethod")
  }
  /* method="dialog" closes the dialog; it does not navigate. */
  if (method.trim().toLowerCase() === "dialog") {
    return
  }
  event.preventDefault()
  let fields = {}
  try {
    fields = Object.fromEntries(submitter !== null ? new FormData(form, submitter) : new FormData(form))
  } catch (error) {
    fields = {}
  }
  logBlocked("form submission blocked", {
    method: method,
    action: form.getAttribute("action") || "",
    fields: fields
  })
  return
}

function onNavigate(event) {
  const crossDocument = event.destination !== null && event.destination.sameDocument === false
  const leaves = event.navigationType === "push" || event.navigationType === "replace"
  if (event.cancelable !== true || crossDocument === false || leaves === false) {
    return
  }
  if (event.downloadRequest !== null && event.downloadRequest !== undefined) {
    return
  }
  const url = event.destination.url
  /* The sandbox page loads each run into the frame as a new srcdoc document. */
  if (url.startsWith("about:") === true) {
    return
  }
  event.preventDefault()
  const fragment = ownFragment("", url)
  if (fragment !== null) {
    setTimeout(() => goToFragment(fragment), 0)
  } else {
    logBlocked("navigation blocked", { url: url })
  }
  return
}

function guardNavigation() {
  window.addEventListener("click", onLinkClick)
  window.addEventListener("submit", onFormSubmit)
  if (window.navigation !== undefined && window.navigation !== null) {
    window.navigation.addEventListener("navigate", onNavigate)
  }
  return
}


/* ----- running the example ---------------------------------------------- */

function holdScripts(fragment) {
  for (const script of fragment.querySelectorAll("script")) {
    const type = (script.getAttribute("type") || "").trim()
    if (EXECUTABLE_TYPE.test(type) === true) {
      script.setAttribute("data-mj-held", type)
      script.setAttribute("type", HELD_TYPE)
    }
  }
  return
}

/*
 * Replace a held script with a fresh, executable copy. An inline classic
 * script runs during the replace; an external one is awaited so scripts
 * keep their document order.
 */
function releaseScript(held) {
  const released = new Promise((resolve) => {
    const fresh = document.createElement("script")
    for (const attribute of Array.from(held.attributes)) {
      if (attribute.name !== "type" && attribute.name !== "data-mj-held") {
        fresh.setAttribute(attribute.name, attribute.value)
      }
    }
    const originalType = held.getAttribute("data-mj-held")
    if (originalType !== null && originalType !== "") {
      fresh.setAttribute("type", originalType)
    }
    const external = fresh.hasAttribute("src")
    if (external === true) {
      fresh.async = false
      fresh.addEventListener("load", () => resolve(), { once: true })
      fresh.addEventListener("error", () => resolve(), { once: true })
    } else {
      fresh.textContent = held.textContent
    }
    held.replaceWith(fresh)
    if (external === false) {
      resolve()
    }
  })
  return released
}

function timeout(milliseconds) {
  const timer = new Promise((resolve) => {
    setTimeout(resolve, milliseconds)
  })
  return timer
}

async function start() {
  const template = document.getElementById("mj-sandbox-markup")
  if (template !== null) {
    holdScripts(template.content)
    const fragment = document.importNode(template.content, true)
    template.remove()
    document.body.append(fragment)
  }
  watchSize()
  guardNavigation()

  const outcome = await loadLibrary()
  window.mjSandbox.timing.library = performance.now()
  if (outcome === "retrying") {
    return
  }

  /*
   * index.js defines every element while it evaluates, so normally nothing
   * is pending here and the held scripts run in the same task as the
   * upgrade: nothing can observe a defined element before its scripts ran.
   */
  if (outcome === "loaded") {
    const pending = []
    for (const tag of pendingLibraryTags()) {
      pending.push(customElements.whenDefined(tag))
    }
    if (pending.length > 0) {
      await Promise.race([Promise.all(pending), timeout(DEFINE_TIMEOUT_MS)])
    }
  }

  window.mjSandbox.timing.scripts = performance.now()
  for (const held of Array.from(document.querySelectorAll('script[type="' + HELD_TYPE + '"]'))) {
    if (held.hasAttribute("src") === true) {
      await releaseScript(held)
    } else {
      releaseScript(held)
    }
  }

  const source = typeof config.script === "string" ? config.script : ""
  if (source.trim() !== "") {
    const moduleScript = document.createElement("script")
    moduleScript.type = "module"
    moduleScript.textContent = source + "\n;window.mjSandbox._scriptDone(" + config.run + ")\n"
    /* A module that fails to parse or throws still completes the run. */
    window.addEventListener("error", () => finish(), { once: true })
    document.head.append(moduleScript)
  } else {
    finish()
  }
  return
}

start()
