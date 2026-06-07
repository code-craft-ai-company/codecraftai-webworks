/*
 * announcer.js
 *
 * Live-region announcement service. A single pair of visually-hidden live
 * regions (polite + assertive) is appended to the document; components route
 * status messages through `announce()` so screen readers are notified without
 * each component shipping its own live region.
 */

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

function ensureRegions() {
  if (politeRegion === null) {
    politeRegion = buildRegion("polite")
    document.body.appendChild(politeRegion)
  }
  if (assertiveRegion === null) {
    assertiveRegion = buildRegion("assertive")
    document.body.appendChild(assertiveRegion)
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
