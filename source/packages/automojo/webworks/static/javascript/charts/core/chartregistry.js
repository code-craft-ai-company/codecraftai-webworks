/*
 * chartregistry.js
 *
 * Controller/part coordination helpers. A chart part finds its controlling
 * <mj-chart> either by the `chart` attribute (the controller's id -- lets a
 * part live anywhere in the document) or by the nearest ancestor.
 */

const CONTROLLER_TAG = "mj-chart";


function _isController(node) {
  /*
   * True when a node is an <mj-chart> controller element.
   */
  const tag = node !== null && node !== undefined ? node.tagName : null
  const matches = tag !== null && tag !== undefined &&
    tag.toLowerCase() === CONTROLLER_TAG
  return matches
}


export function resolveController(part) {
  /*
   * Resolve the <mj-chart> controller for a chart part.
   *
   * :param part: The chart part element.
   * :returns: The controller element, or null when none is found.
   */
  const id = part.getAttribute("chart")
  if (id !== null && id.trim().length > 0) {
    const root = part.getRootNode()
    let found = null
    if (root !== null && typeof root.getElementById === "function") {
      found = root.getElementById(id.trim())
    }
    if (found === null) {
      found = document.getElementById(id.trim())
    }
    if (found !== null && _isController(found) === true) {
      return found
    }
  }

  /* Fall back to the nearest ancestor controller, crossing shadow roots. */
  let node = part.parentNode
  while (node !== null && node !== undefined) {
    if (_isController(node) === true) {
      return node
    }
    if (node.host !== undefined && node.host !== null) {
      node = node.host
    } else {
      node = node.parentNode
    }
  }

  return null
}
