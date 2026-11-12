/*
 * aria.js
 *
 * Field-association helpers shared by the field-companion components
 * (<mj-label>, <mj-help-text>, <mj-error-message>, <mj-character-counter>,
 * <mj-validation-summary>): resolve a `for` target in the right tree, find
 * the node inside an mj-* control that carries its ARIA state, and attach
 * aria-labelledby / aria-describedby relationships to it -- by id when both
 * ends are in the same tree, by element reflection across a shadow boundary.
 *
 * Usage:
 *   import { findById, addAriaReference } from "../core/aria.js";
 *   const control = findById(this, this.getAttribute("for"))
 *   addAriaReference(control, "describedby", this._messageEl)
 */

/*
 * The node inside an mj-* control that takes focus and therefore carries the
 * ARIA state assistive technology reads. Mirrors the lookup in
 * `MjElement.focus()`, without excluding disabled controls.
 */
const ARIA_TARGET_SELECTOR =
  "[data-mj-focus-target], input:not([type='hidden']), textarea, select, " +
  "[contenteditable]:not([contenteditable='false']), [role='textbox'], [role='combobox'], " +
  "[role='slider'], [role='spinbutton'], [role='listbox'], [role='radiogroup'], [role='group']";

const ARIA_RELATIONS = {
  labelledby: { attribute: "aria-labelledby", property: "ariaLabelledByElements" },
  describedby: { attribute: "aria-describedby", property: "ariaDescribedByElements" }
};

/*
 * Relationships attached from outside a control's shadow root, keyed by the
 * control host. Each record remembers the ARIA target they were applied to
 * and the observer that re-applies them when the control rewrites its own
 * `aria-describedby` / `aria-labelledby` or re-renders its shadow DOM.
 */
const EXTERNAL_REFERENCES = new WeakMap();

/*
 * Resolve `id` in the tree that contains `element`: the document, or the
 * shadow root when the element lives inside another component. Returns null
 * when the id is empty or not found.
 */
export function findById(element, id) {
  let found = null

  if (id !== null && id !== undefined && id.length > 0) {
    const root = element.getRootNode()
    if (root !== null && typeof root.getElementById === "function") {
      found = root.getElementById(id)
    } else if (root !== null && typeof root.querySelector === "function") {
      found = root.querySelector(`#${CSS.escape(id)}`)
    }
  }

  return found
}

/*
 * The node that carries ARIA state for `control`. A native control carries
 * its own; an mj-* control delegates to the focus target in its shadow root.
 */
export function ariaTargetOf(control) {
  let target = control

  if (control !== null && control !== undefined) {
    const shadow = control.shadowRoot
    if (shadow !== null && shadow !== undefined) {
      const inner = shadow.querySelector(ARIA_TARGET_SELECTOR)
      if (inner !== null) {
        target = inner
      }
    }
  }

  return target
}

function readIdTokens(element, attribute) {
  const current = element.getAttribute(attribute) || ""
  const tokens = current.split(/\s+/).filter((token) => token.length > 0)
  return tokens
}

function writeIdTokens(element, attribute, tokens) {
  if (tokens.length > 0) {
    element.setAttribute(attribute, tokens.join(" "))
  } else {
    element.removeAttribute(attribute)
  }
  return
}

function addIdToken(element, attribute, id) {
  const tokens = readIdTokens(element, attribute)
  if (tokens.indexOf(id) === -1) {
    tokens.push(id)
    writeIdTokens(element, attribute, tokens)
  }
  return
}

function removeIdToken(element, attribute, id) {
  const tokens = readIdTokens(element, attribute)
  const remaining = tokens.filter((token) => token !== id)
  if (remaining.length !== tokens.length) {
    writeIdTokens(element, attribute, remaining)
  }
  return
}

/*
 * Write the external relationships of `record` onto its ARIA target with
 * element reflection (`ariaDescribedByElements` ...), which is the only way
 * a node inside a shadow root can reference an element of an enclosing
 * tree. The ids the control set itself are kept.
 */
function applyExternalReferences(record) {
  const names = Object.keys(ARIA_RELATIONS)

  for (let index = 0; index < names.length; index = index + 1) {
    const relation = ARIA_RELATIONS[names[index]]
    const sources = record.sources[names[index]]
    const target = record.target

    const current = target[relation.property]
    const existing = current !== null && current !== undefined ? Array.from(current) : []

    let missing = false
    for (let position = 0; position < sources.length; position = position + 1) {
      if (existing.indexOf(sources[position]) === -1) {
        missing = true
      }
    }

    if (missing === true) {
      const merged = existing.slice()
      for (let position = 0; position < sources.length; position = position + 1) {
        if (merged.indexOf(sources[position]) === -1) {
          merged.push(sources[position])
        }
      }
      target[relation.property] = merged
    }
  }

  return
}

/*
 * Remove `source` from an element-reflected relationship of `target`,
 * leaving the other referenced elements in place.
 */
function dropReflectedReference(target, relation, source) {
  const current = target[relation.property]
  const existing = current !== null && current !== undefined ? Array.from(current) : []
  const position = existing.indexOf(source)

  if (position !== -1) {
    existing.splice(position, 1)
    if (existing.length > 0) {
      target[relation.property] = existing
    } else {
      target[relation.property] = null
      target.removeAttribute(relation.attribute)
    }
  }
  return
}

function observeExternalTarget(control, record) {
  if (record.observer !== null) {
    record.observer.disconnect()
  }

  record.observer = new MutationObserver(() => {
    const target = ariaTargetOf(control)
    if (target !== record.target) {
      /* The control re-rendered: move the relationships to the new node. */
      record.target = target
      observeExternalTarget(control, record)
    }
    applyExternalReferences(record)
  })

  record.observer.observe(record.target, {
    attributes: true,
    attributeFilter: [ARIA_RELATIONS.labelledby.attribute, ARIA_RELATIONS.describedby.attribute]
  })
  record.observer.observe(control.shadowRoot, { childList: true, subtree: true })
  return
}

/*
 * Add `source` to the `relation` ("labelledby" or "describedby") of
 * `control`. When the node that carries the control's ARIA state is in the
 * same tree as `source`, the id is added to the attribute; when it is inside
 * the control's shadow root, element reflection is used so the reference
 * resolves across the shadow boundary. `source` must have an id.
 */
export function addAriaReference(control, relationName, source) {
  const relation = ARIA_RELATIONS[relationName]
  const target = ariaTargetOf(control)
  const sameTree = target === control || target.getRootNode() === source.getRootNode()
  const reflectionSupported = relation.property in Element.prototype

  if (sameTree === true || reflectionSupported === false) {
    addIdToken(sameTree === true ? target : control, relation.attribute, source.id)
    return
  }

  let record = EXTERNAL_REFERENCES.get(control)
  if (record === undefined) {
    record = { target: target, observer: null, sources: { labelledby: [], describedby: [] } }
    EXTERNAL_REFERENCES.set(control, record)
  }

  if (record.target !== target) {
    record.target = target
  }
  if (record.sources[relationName].indexOf(source) === -1) {
    record.sources[relationName].push(source)
  }

  applyExternalReferences(record)
  observeExternalTarget(control, record)
  return
}

/* Undo `addAriaReference` for `source`. Safe to call when nothing was added. */
export function removeAriaReference(control, relationName, source) {
  const relation = ARIA_RELATIONS[relationName]

  removeIdToken(control, relation.attribute, source.id)

  const record = EXTERNAL_REFERENCES.get(control)
  if (record !== undefined) {
    const sources = record.sources[relationName]
    const position = sources.indexOf(source)
    if (position !== -1) {
      sources.splice(position, 1)
    }

    if (record.observer !== null) {
      /* Stop observing before editing so the removal is not re-applied. */
      record.observer.disconnect()
      record.observer = null
    }
    dropReflectedReference(record.target, relation, source)

    const remaining = record.sources.labelledby.length + record.sources.describedby.length
    if (remaining > 0) {
      observeExternalTarget(control, record)
    } else {
      EXTERNAL_REFERENCES.delete(control)
    }
  } else {
    const target = ariaTargetOf(control)
    if (target !== control) {
      removeIdToken(target, relation.attribute, source.id)
    }
  }
  return
}

/*
 * A custom element that has not been upgraded yet has no shadow root, so
 * the node that will carry its ARIA state cannot be found. That is the case
 * before its definition is registered, and also while a parsed fragment is
 * still being upgraded element by element. When `control` is not upgraded,
 * `onReady` is called once it is (after the current upgrade reactions) and
 * true is returned; otherwise false is returned and nothing is scheduled.
 */
export function deferUntilDefined(control, onReady) {
  const isCustom = control.localName.indexOf("-") !== -1
  const pending = isCustom === true && control.matches(":defined") === false

  if (pending === true) {
    customElements.whenDefined(control.localName).then(() => {
      onReady()
    })
  }
  return pending
}

/*
 * Watch the tree of `element` until an element with `id` exists, then call
 * `onFound(target)` once. Returns a function that stops watching.
 */
export function waitForId(element, id, onFound) {
  const root = element.getRootNode()
  const scope = root instanceof Document ? root.documentElement : root

  let observer = new MutationObserver(() => {
    const target = findById(element, id)
    if (target !== null && observer !== null) {
      observer.disconnect()
      observer = null
      onFound(target)
    }
  })
  observer.observe(scope, { childList: true, subtree: true })

  const stop = () => {
    if (observer !== null) {
      observer.disconnect()
      observer = null
    }
  }
  return stop
}
