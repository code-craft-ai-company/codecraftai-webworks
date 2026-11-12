/*
 * announcer.js
 *
 * Live-region announcement service. A single pair of visually-hidden live
 * regions (polite + assertive) is appended to the document; components route
 * status messages through `announce()` so screen readers are notified without
 * each component shipping its own live region.
 *
 * While a modal surface (dialog, drawer, ...) is open everything outside it
 * is inert and hidden from assistive technology, so the regions live inside
 * the topmost modal surface then (core/overlay.js moves them there when the
 * modal opens and back to <body> when it closes).
 */

import { topModalSurface } from "./overlay.js";

let politeRegion = null;
let assertiveRegion = null;

function buildRegion(politeness) {
  const region = document.createElement("div")
  region.setAttribute("aria-live", politeness)
  region.setAttribute("aria-atomic", "true")
  region.setAttribute("role", politeness === "assertive" ? "alert" : "status")
  region.className = "mj-live-region"
  region.style.position = "absolute"
  region.style.width = "1px"
  region.style.height = "1px"
  region.style.margin = "-1px"
  region.style.padding = "0"
  region.style.overflow = "hidden"
  region.style.clip = "rect(0 0 0 0)"
  region.style.clipPath = "inset(50%)"
  region.style.whiteSpace = "nowrap"
  return region
}

/*
 * Make sure both live regions exist and sit where assistive technology can
 * read them: inside the topmost open modal surface, otherwise in the current
 * body. A region that was removed (the page replaced document.body, or a
 * script cleared it) is attached again, because a detached region is silent.
 */
function ensureRegions() {
  if (politeRegion === null) {
    politeRegion = buildRegion("polite")
  }
  if (assertiveRegion === null) {
    assertiveRegion = buildRegion("assertive")
  }

  let container = topModalSurface()
  if (container === null) {
    container = document.body
  }

  if (container !== null) {
    if (politeRegion.isConnected === false || politeRegion.parentNode !== container) {
      container.appendChild(politeRegion)
    }
    if (assertiveRegion.isConnected === false || assertiveRegion.parentNode !== container) {
      container.appendChild(assertiveRegion)
    }
  }
  return
}

/*
 * Announce `message` to assistive technology.
 * politeness: "polite" (default) or "assertive".
 */
export function announce(message, politeness) {
  if (message === null || message === undefined || message === "") {
    return
  }

  ensureRegions()
  const region = politeness === "assertive" ? assertiveRegion : politeRegion

  /* Clear then set on the next frame so repeated identical messages re-fire. */
  region.textContent = ""
  window.requestAnimationFrame(() => {
    region.textContent = message
  })
  return
}
