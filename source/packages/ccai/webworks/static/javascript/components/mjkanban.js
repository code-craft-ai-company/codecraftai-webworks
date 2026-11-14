/*
 * mjkanban.js
 *
 * <mj-kanban> -- multi-column card board for workflow visualization.
 * Supports pointer drag-and-drop (HTML5 drag for mouse, pointer events for
 * touch and pen) and a keyboard move mode. WIP limits, live region
 * announcements for screen readers.
 *
 * Keyboard: Tab reaches each card and its drag handle. Enter / Space on a
 * card emits `mj-card-click`. Enter / Space on a handle starts move mode:
 * ArrowLeft / ArrowRight pick the column, ArrowUp / ArrowDown the position,
 * Enter (or Space) drops the card there, Escape cancels. Focus stays on the
 * moved card's handle.
 *
 * Positions (`toIndex`) count the cards of the target column WITHOUT the
 * moved card, so moving a card onto its own position is a no-op.
 *
 * Slots: `column-header-[id]`, `add-card-[id]`, `empty-[id]` per column, and
 * `loading`. `renderCard(card)` may return a Node or a string; a string is
 * inserted as markup, so escape interpolated data with core/html.js.
 *
 * Events: mj-card-click, mj-card-move-start (cancelable), mj-card-move
 * (cancelable), mj-card-move-complete, mj-card-move-error,
 * mj-col-wip-exceeded, mj-board-error.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
  font: inherit;
  color: var(--mj-text);
}

.board {
  display: flex;
  gap: var(--mj-kanban-col-gap, 12px);
  overflow-x: auto;
  align-items: flex-start;
  padding: var(--mj-space-3);
  min-height: 200px;
}

:host([layout="fluid"]) .board { flex-wrap: wrap; }

.column {
  flex: 0 0 var(--mj-kanban-col-width, 280px);
  min-width: var(--mj-kanban-col-width, 280px);
  background: var(--mj-kanban-col-bg, var(--mj-bg-subtle));
  border-radius: var(--mj-radius-md);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--mj-border);
}

.column-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--mj-space-3);
  font-weight: var(--mj-font-weight-medium);
  border-block-end: 1px solid var(--mj-border);
  background: var(--mj-surface);
}

.col-title { font-size: var(--mj-font-size-sm); }

.wip-badge {
  font-size: var(--mj-font-size-xs);
  padding: 2px 6px;
  border-radius: var(--mj-radius-pill);
  background: var(--mj-bg-muted);
  color: var(--mj-text-muted);
}
.wip-badge.at-limit { color: var(--mj-kanban-wip-ok-color, var(--mj-text)); }
.wip-badge.exceeded {
  background: var(--mj-color-warning-surface);
  color: var(--mj-kanban-wip-exceeded-color, var(--mj-color-warning));
}

.column-body {
  padding: var(--mj-space-2);
  display: flex;
  flex-direction: column;
  gap: var(--mj-kanban-card-gap, 8px);
  min-height: 80px;
  flex: 1;
}
.column-body.drag-over { background: color-mix(in srgb, var(--mj-accent) 8%, transparent); }

.card {
  background: var(--mj-kanban-card-bg, var(--mj-surface));
  border-radius: var(--mj-kanban-card-radius, var(--mj-radius-md));
  border: 1px solid var(--mj-border);
  padding: var(--mj-space-3);
  cursor: pointer;
  user-select: none;
  display: flex;
  align-items: flex-start;
  gap: var(--mj-space-2);
  box-shadow: var(--mj-elevation-1);
  transition: box-shadow var(--mj-motion-fast) var(--mj-motion-ease);
}
.card:hover { box-shadow: var(--mj-elevation-2); }
.card:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.card.dragging { opacity: var(--mj-kanban-drag-opacity, 0.5); }
.card.in-move-mode { outline: 2px solid var(--mj-accent); }

.card-handle {
  cursor: grab;
  color: var(--mj-text-muted);
  font-size: 1.1em;
  flex-shrink: 0;
  background: none;
  border: none;
  padding: 0;
  line-height: 1;
  touch-action: none;
}
.card-handle:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
:host([mode="readonly"]) .card-handle { display: none; }

.card-content { flex: 1; min-width: 0; font-size: var(--mj-font-size-sm); }
.card-title { font-weight: var(--mj-font-weight-medium); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.drop-zone {
  height: 4px;
  border-radius: 2px;
  background: transparent;
  transition: background var(--mj-motion-fast);
}
.drop-zone.active { background: var(--mj-kanban-drop-zone-color, var(--mj-accent)); height: 12px; }

.status-region {
  position: absolute; width: 1px; height: 1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;
}

.move-instructions {
  display: none;
  padding: var(--mj-space-2) var(--mj-space-3);
  font-size: var(--mj-font-size-xs);
  background: var(--mj-color-info-surface);
  color: var(--mj-color-info);
  border-block-start: 1px solid var(--mj-border);
}
.move-instructions.visible { display: block; }

.column-footer:empty { display: none; }
.column-footer { padding: 0 var(--mj-space-2) var(--mj-space-2); }

.loading-region {
  padding: var(--mj-space-3);
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
}
.loading-region[hidden] { display: none; }
`;

/* Pointer travel (px) before a touch / pen press on a handle becomes a drag. */
const TOUCH_DRAG_THRESHOLD = 6;

export class MjKanban extends MjElement {
  static tagName = "mj-kanban";
  static styles = STYLES;
  static watched = ["mode", "layout", "col-width", "wip-limits", "loading", "label", "aria-label"];

  constructor() {
    super()
    this._columns = []
    this._dataSource = null
    this._renderCard = null

    /* A move in progress (mouse drag, touch drag or keyboard). */
    this._dragState = null
    this._moveMode = null
    this._pointerDrag = null

    /* After a re-render, focus goes to this card's handle (or the card). */
    this._restoreFocus = null
    this._dropZoneEl = null
    this._boardId = nextId("mj-kanban")
  }

  render() {
    const markup = `
      <div class="loading-region" part="loading" hidden><slot name="loading"></slot></div>
      <div class="board" part="board" role="region"></div>
      <div class="status-region" role="status" aria-live="assertive" aria-atomic="true"></div>
    `
    return markup
  }

  afterRender() {
    this._board = this.$(".board")
    this._statusRegion = this.$(".status-region")
    this._loadingRegion = this.$(".loading-region")
    this.$("slot[name='loading']").textContent = t("mj.kanban.loading")
    this._moveMode = null
    this._dragState = null
    this._pointerDrag = null
    this._dropZoneEl = null

    /* Every interaction is delegated from the board: re-renders add nothing. */
    this.listen(this._board, "click", this._onBoardClick.bind(this))
    this.listen(this._board, "keydown", this._onBoardKeydown.bind(this))
    this.listen(this._board, "dragstart", this._onDragStart.bind(this))
    this.listen(this._board, "dragend", this._onDragEnd.bind(this))
    this.listen(this._board, "dragover", this._onDragOver.bind(this))
    this.listen(this._board, "dragleave", this._onDragLeave.bind(this))
    this.listen(this._board, "drop", this._onDrop.bind(this))
    this.listen(this._board, "pointerdown", this._onPointerDown.bind(this))
    this.listen(this._board, "pointermove", this._onPointerMove.bind(this))
    this.listen(this._board, "pointerup", this._onPointerUp.bind(this))
    this.listen(this._board, "pointercancel", this._onPointerCancel.bind(this))
    this.listen(this._board, "focusout", this._onBoardFocusOut.bind(this))

    this._syncLabel()
    this._syncColWidth()
    this._syncLoading()
    this._renderBoard()

    if (this._dataSource !== null) {
      this._loadBoard()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._board === undefined || this._board === null) {
      return
    }
    if (name === "loading") {
      this._syncLoading()
    }
    if (name === "label" || name === "aria-label") {
      this._syncLabel()
    }
    if (name === "col-width") {
      this._syncColWidth()
    }
    if ((name === "mode" || name === "wip-limits") && oldValue !== newValue) {
      if (this._moveMode !== null) {
        this._cancelMoveMode()
      }
      this._renderBoard()
    }
    return
  }

  _isReadonly() {
    const readonly = (this.getAttribute("mode") || "interactive") === "readonly"
    return readonly
  }

  _syncLabel() {
    const label = this.getAttribute("label") || this.getAttribute("aria-label") || t("mj.kanban.label")
    this._board.setAttribute("aria-label", label)
    return
  }

  /* `col-width` (px number or CSS length) sets --mj-kanban-col-width. */
  _syncColWidth() {
    const raw = this.getAttribute("col-width")
    if (raw !== null && raw.trim().length > 0) {
      const text = raw.trim()
      const isNumber = /^\d+(\.\d+)?$/.test(text)
      this._board.style.setProperty("--mj-kanban-col-width", isNumber === true ? `${text}px` : text)
    } else {
      this._board.style.removeProperty("--mj-kanban-col-width")
    }
    return
  }

  _syncLoading() {
    const loading = this.hasAttribute("loading")
    this._board.setAttribute("aria-busy", loading === true ? "true" : "false")
    this._loadingRegion.hidden = loading === false
    return
  }

  _loadBoard() {
    if (this._dataSource === null || typeof this._dataSource.fetchBoard !== "function") {
      return
    }
    this.reflectBoolean("loading", true)
    let pending = null
    try {
      pending = Promise.resolve(this._dataSource.fetchBoard())
    } catch (error) {
      pending = Promise.reject(error)
    }
    pending.then((cols) => {
      this.reflectBoolean("loading", false)
      this._columns = Array.isArray(cols) === true ? cols : []
      this._renderBoard()
      return
    }).catch((error) => {
      this.reflectBoolean("loading", false)
      this.emit("mj-board-error", { error: error })
      announce(t("mj.kanban.loadFailed"), "assertive")
    })
    return
  }

  /* ----- lookup helpers ----- */

  _cardsOf(col) {
    const cards = col !== undefined && Array.isArray(col.cards) === true ? col.cards : []
    return cards
  }

  _columnById(colId) {
    const col = this._columns.find((c) => String(c.id) === String(colId))
    return col
  }

  _columnIndex(colId) {
    const index = this._columns.findIndex((c) => String(c.id) === String(colId))
    return index
  }

  _cardIndex(col, cardId) {
    const index = this._cardsOf(col).findIndex((c) => String(c.id) === String(cardId))
    return index
  }

  _findCardElement(cardId) {
    let found = null
    const cards = this._board.querySelectorAll(".card")
    for (let i = 0; i < cards.length; i = i + 1) {
      if (cards[i].getAttribute("data-card-id") === String(cardId)) {
        found = cards[i]
        break
      }
    }
    return found
  }

  _findColumnBody(colId) {
    let found = null
    const bodies = this._board.querySelectorAll(".column-body")
    for (let i = 0; i < bodies.length; i = i + 1) {
      if (bodies[i].getAttribute("data-col-id") === String(colId)) {
        found = bodies[i]
        break
      }
    }
    return found
  }

  /* ----- rendering ----- */

  _renderBoard() {
    const focusedCard = this._focusedCardInfo()
    this._dropZoneEl = null
    this._board.replaceChildren()

    for (let ci = 0; ci < this._columns.length; ci = ci + 1) {
      const col = this._columns[ci]
      const colEl = this._buildColumn(col, ci)
      this._board.appendChild(colEl)
    }

    /* Put focus back on the card it was on (or the card that just moved). */
    const target = this._restoreFocus !== null ? this._restoreFocus : focusedCard
    this._restoreFocus = null
    if (target !== null) {
      const cardEl = this._findCardElement(target.cardId)
      if (cardEl !== null) {
        const handle = cardEl.querySelector(".card-handle")
        if (target.onHandle === true && handle !== null) {
          handle.focus()
        } else {
          cardEl.focus()
        }
      }
    }
    return
  }

  /* The card focus is in, if any, and whether it is on the handle. */
  _focusedCardInfo() {
    let info = null
    const active = this.shadowRoot.activeElement
    if (active !== null && active !== undefined && this._board.contains(active) === true) {
      const cardEl = active.closest(".card")
      if (cardEl !== null) {
        info = { cardId: cardEl.getAttribute("data-card-id"), onHandle: active.classList.contains("card-handle") }
      }
    }
    return info
  }

  /* WIP state of a column: "none", "ok", "at-limit" or "exceeded". */
  _wipState(col) {
    let state = "none"
    if (this.hasAttribute("wip-limits") === true && typeof col.wipLimit === "number") {
      const count = this._cardsOf(col).length
      if (count > col.wipLimit) {
        state = "exceeded"
      } else if (count === col.wipLimit) {
        state = "at-limit"
      } else {
        state = "ok"
      }
    }
    return state
  }

  _buildColumn(col, colIdx) {
    const cards = this._cardsOf(col)
    const label = col.label !== undefined && col.label !== null ? String(col.label) : String(col.id)

    const colEl = document.createElement("section")
    colEl.className = "column"
    colEl.setAttribute("part", "column")
    colEl.setAttribute("role", "group")
    colEl.setAttribute("aria-label", t("mj.kanban.columnLabel", { label: label, count: cards.length }))
    colEl.setAttribute("data-col-id", String(col.id))

    const header = document.createElement("div")
    header.className = "column-header"
    header.setAttribute("part", "column-header")

    const title = document.createElement("span")
    title.className = "col-title"
    title.textContent = label
    header.appendChild(title)

    const headerSlot = document.createElement("slot")
    headerSlot.setAttribute("name", `column-header-${col.id}`)
    header.appendChild(headerSlot)

    const wip = this._wipState(col)
    if (wip !== "none") {
      const badge = document.createElement("span")
      badge.className = wip === "ok" ? "wip-badge" : `wip-badge ${wip}`
      badge.setAttribute("part", "wip-indicator")
      const wipParams = { count: cards.length, limit: col.wipLimit }
      let wipLabel = t("mj.kanban.wipLimit", wipParams)
      if (wip === "exceeded") {
        wipLabel = t("mj.kanban.wipLimitExceeded", wipParams)
      } else if (wip === "at-limit") {
        wipLabel = t("mj.kanban.wipLimitAtLimit", wipParams)
      }
      badge.setAttribute("aria-label", wipLabel)
      badge.textContent = `${cards.length}/${col.wipLimit}`
      header.appendChild(badge)
    }

    colEl.appendChild(header)

    const instructions = document.createElement("div")
    instructions.className = "move-instructions"
    instructions.textContent = t("mj.kanban.moveInstructions")
    colEl.appendChild(instructions)

    /*
     * The body is the drop target. While it holds cards it is the column's
     * list. An empty column shows its empty-[id] slot there instead, and a
     * list may own only list items, so the empty body is a plain container
     * (the column group's name already says it holds 0 cards).
     */
    const body = document.createElement("div")
    body.className = "column-body"
    body.setAttribute("part", "column-body")
    body.setAttribute("data-col-id", String(col.id))
    colEl.appendChild(body)

    if (cards.length === 0) {
      const emptySlot = document.createElement("slot")
      emptySlot.setAttribute("name", `empty-${col.id}`)
      body.appendChild(emptySlot)
    } else {
      body.setAttribute("role", "list")
      body.setAttribute("aria-label", label)
    }

    for (let ki = 0; ki < cards.length; ki = ki + 1) {
      const cardEl = this._buildCard(cards[ki], col.id, ki)
      body.appendChild(cardEl)
    }

    const footer = document.createElement("div")
    footer.className = "column-footer"
    footer.setAttribute("part", "column-footer")
    const addSlot = document.createElement("slot")
    addSlot.setAttribute("name", `add-card-${col.id}`)
    footer.appendChild(addSlot)
    colEl.appendChild(footer)

    return colEl
  }

  _buildCard(card, colId, cardIdx) {
    const cardTitle = card.title !== undefined && card.title !== null ? String(card.title) : String(card.id)
    const cardEl = document.createElement("div")
    cardEl.className = "card"
    cardEl.setAttribute("part", "card")
    cardEl.setAttribute("role", "listitem")
    cardEl.setAttribute("data-card-id", String(card.id))
    cardEl.setAttribute("data-col-id", String(colId))
    cardEl.setAttribute("tabindex", "0")
    cardEl.setAttribute("aria-label", cardTitle)

    if (this._isReadonly() === false) {
      const handle = document.createElement("button")
      handle.type = "button"
      handle.className = "card-handle"
      handle.setAttribute("part", "card-handle")
      handle.setAttribute("aria-label", t("mj.kanban.moveCard", { title: cardTitle }))
      handle.setAttribute("aria-pressed", "false")
      handle.textContent = "⠿"
      handle.setAttribute("draggable", "true")
      cardEl.appendChild(handle)
    }

    const content = document.createElement("div")
    content.className = "card-content"

    if (this._renderCard !== null) {
      const rendered = this._renderCard(card)
      if (rendered instanceof Node) {
        content.appendChild(rendered)
      } else if (typeof rendered === "string") {
        /* Documented contract: a string is markup the caller has escaped. */
        content.innerHTML = rendered
      } else if (rendered !== null && rendered !== undefined && typeof rendered.markup === "string") {
        /* Result of the `html` tag from core/html.js. */
        content.innerHTML = rendered.markup
      }
    } else {
      const titleEl = document.createElement("div")
      titleEl.className = "card-title"
      titleEl.textContent = cardTitle
      titleEl.setAttribute("title", cardTitle)
      content.appendChild(titleEl)
    }

    cardEl.appendChild(content)
    return cardEl
  }

  /* ----- click and keyboard ----- */

  _cardFromEvent(event) {
    let cardEl = null
    if (event.target instanceof Element) {
      cardEl = event.target.closest(".card")
    }
    return cardEl
  }

  _isHandleEvent(event) {
    const onHandle = event.target instanceof Element && event.target.closest(".card-handle") !== null
    return onHandle
  }

  _emitCardClick(cardEl) {
    this.emit("mj-card-click", {
      cardId: cardEl.getAttribute("data-card-id"),
      colId: cardEl.getAttribute("data-col-id")
    })
    return
  }

  _onBoardClick(event) {
    const cardEl = this._cardFromEvent(event)
    if (cardEl === null || this._isHandleEvent(event) === true) {
      return
    }
    this._emitCardClick(cardEl)
    return
  }

  _onBoardKeydown(event) {
    const key = event.key

    if (this._moveMode !== null) {
      this._onMoveModeKeydown(event)
      return
    }

    const cardEl = this._cardFromEvent(event)
    if (cardEl === null) {
      return
    }

    if (this._isHandleEvent(event) === true) {
      if (key === " " || key === "Enter") {
        /* Prevented here so the native button does not also click. */
        event.preventDefault()
        event.stopPropagation()
        this._enterMoveMode(cardEl)
      }
      return
    }

    if (event.target === cardEl && (key === "Enter" || key === " ")) {
      event.preventDefault()
      this._emitCardClick(cardEl)
    }
    return
  }

  /* ----- moves (shared by drag, touch and keyboard) ----- */

  /* Start a move. Returns false when a listener canceled `mj-card-move-start`. */
  _startDrag(cardId, fromColId, fromIndex) {
    const proceed = this.emit("mj-card-move-start", { cardId: cardId, fromColId: fromColId, fromIndex: fromIndex }, { cancelable: true })
    if (proceed === false) {
      this._dragState = null
    } else {
      this._dragState = { cardId: cardId, fromColId: fromColId, fromIndex: fromIndex, completed: false }
    }
    return proceed
  }

  _cancelDrag() {
    this._dragState = null
    this._clearDropZone()
    return
  }

  /* Card data and position of the card element, for starting a move. */
  _cardOrigin(cardEl) {
    const colId = cardEl.getAttribute("data-col-id")
    const cardId = cardEl.getAttribute("data-card-id")
    const col = this._columnById(colId)
    const origin = { cardId: cardId, colId: col !== undefined ? col.id : colId, index: this._cardIndex(col, cardId) }
    return origin
  }

  /*
   * Complete the move in progress. `toIndex` counts the target column's
   * cards without the moved card; the unchanged position is a no-op.
   */
  _completeDrop(toColId, toIndex, refocusHandle) {
    if (this._dragState === null) {
      return
    }
    const ds = this._dragState
    ds.completed = true
    this._dragState = null
    this._clearDropZone()

    const sameColumn = String(ds.fromColId) === String(toColId)
    if (sameColumn === true && ds.fromIndex === toIndex) {
      return
    }

    const proceed = this.emit("mj-card-move", {
      cardId: ds.cardId,
      fromColId: ds.fromColId,
      toColId: toColId,
      toIndex: toIndex
    }, { cancelable: true })

    if (proceed === false) {
      return
    }

    this._moveCardInData(ds.cardId, ds.fromColId, toColId, toIndex)
    if (refocusHandle === true) {
      this._restoreFocus = { cardId: ds.cardId, onHandle: true }
    }
    this._renderBoard()

    const toCol = this._columnById(toColId)
    const toLabel = toCol !== undefined ? toCol.label : toColId
    this._statusRegion.textContent = t("mj.kanban.cardMoved", { column: toLabel, position: toIndex + 1 })

    if (this._dataSource !== null && typeof this._dataSource.moveCard === "function") {
      let pending = null
      try {
        pending = Promise.resolve(this._dataSource.moveCard(ds.cardId, toColId, toIndex))
      } catch (error) {
        pending = Promise.reject(error)
      }
      pending.then(() => {
        this.emit("mj-card-move-complete", {
          cardId: ds.cardId, fromColId: ds.fromColId, toColId: toColId, toIndex: toIndex
        })
        return
      }).catch((err) => {
        this._moveCardInData(ds.cardId, toColId, ds.fromColId, ds.fromIndex)
        this._renderBoard()
        this.emit("mj-card-move-error", { cardId: ds.cardId, error: err })
      })
    } else {
      this.emit("mj-card-move-complete", {
        cardId: ds.cardId, fromColId: ds.fromColId, toColId: toColId, toIndex: toIndex
      })
    }

    if (toCol !== undefined && this._wipState(toCol) === "exceeded") {
      const count = this._cardsOf(toCol).length
      this.emit("mj-col-wip-exceeded", { colId: toColId, count: count, limit: toCol.wipLimit })
    }
    return
  }

  _moveCardInData(cardId, fromColId, toColId, toIndex) {
    const fromCol = this._columnById(fromColId)
    const toCol = this._columnById(toColId)
    if (fromCol === undefined || toCol === undefined) {
      return
    }

    const fromCards = this._cardsOf(fromCol)
    const cardIdx = this._cardIndex(fromCol, cardId)
    if (cardIdx < 0) {
      return
    }

    const card = fromCards[cardIdx]
    fromCol.cards = fromCards.filter((c) => c !== card)

    const toCards = this._cardsOf(toCol)
    const insertAt = Math.max(0, Math.min(toIndex, toCards.length))
    toCards.splice(insertAt, 0, card)
    toCol.cards = toCards
    return
  }

  /*
   * Show the insertion marker in `colId` before the `index`-th card that is
   * not the moved card.
   */
  _showDropZone(colId, index, movingCardId) {
    const body = this._findColumnBody(colId)
    if (body === null) {
      return
    }
    if (this._dropZoneEl === null) {
      this._dropZoneEl = document.createElement("div")
      this._dropZoneEl.className = "drop-zone active"
      this._dropZoneEl.setAttribute("part", "drop-zone")
      this._dropZoneEl.setAttribute("aria-hidden", "true")
    }
    const others = Array.from(body.querySelectorAll(".card")).filter((el) => el.getAttribute("data-card-id") !== String(movingCardId))
    const before = index < others.length ? others[index] : null
    body.insertBefore(this._dropZoneEl, before)
    return
  }

  _clearDropZone() {
    if (this._dropZoneEl !== null) {
      this._dropZoneEl.remove()
    }
    const highlighted = this._board.querySelectorAll(".column-body.drag-over")
    for (let i = 0; i < highlighted.length; i = i + 1) {
      highlighted[i].classList.remove("drag-over")
    }
    return
  }

  /* The insertion index for a pointer at `clientY` over a column body. */
  _indexFromPointer(body, clientY, movingCardId) {
    const others = Array.from(body.querySelectorAll(".card")).filter((el) => el.getAttribute("data-card-id") !== String(movingCardId))
    let index = others.length
    for (let i = 0; i < others.length; i = i + 1) {
      const rect = others[i].getBoundingClientRect()
      if (clientY < rect.top + rect.height / 2) {
        index = i
        break
      }
    }
    return index
  }

  _announceTarget(colId, index) {
    const col = this._columnById(colId)
    const label = col !== undefined ? col.label : colId
    this._statusRegion.textContent = t("mj.kanban.movingTo", { column: label, position: index + 1 })
    return
  }

  /* ----- mouse: HTML5 drag and drop ----- */

  _onDragStart(event) {
    const cardEl = this._cardFromEvent(event)
    if (cardEl === null || this._isHandleEvent(event) === false || this._isReadonly() === true) {
      return
    }
    const origin = this._cardOrigin(cardEl)
    if (this._startDrag(origin.cardId, origin.colId, origin.index) === false) {
      event.preventDefault()
      return
    }
    if (event.dataTransfer !== null && event.dataTransfer !== undefined) {
      /* Firefox starts a drag only when data is set. */
      event.dataTransfer.setData("text/plain", String(origin.cardId))
      event.dataTransfer.effectAllowed = "move"
    }
    cardEl.classList.add("dragging")
    return
  }

  _onDragEnd(event) {
    const cardEl = this._cardFromEvent(event)
    if (cardEl !== null) {
      cardEl.classList.remove("dragging")
    }
    if (this._dragState !== null && this._dragState.completed === false) {
      this._cancelDrag()
    }
    return
  }

  _bodyFromEvent(event) {
    let body = null
    if (event.target instanceof Element) {
      const colEl = event.target.closest(".column")
      if (colEl !== null) {
        body = colEl.querySelector(".column-body")
      }
    }
    return body
  }

  _onDragOver(event) {
    const body = this._bodyFromEvent(event)
    if (body === null || this._dragState === null) {
      return
    }
    event.preventDefault()
    if (event.dataTransfer !== null && event.dataTransfer !== undefined) {
      event.dataTransfer.dropEffect = "move"
    }
    const colId = body.getAttribute("data-col-id")
    const index = this._indexFromPointer(body, event.clientY, this._dragState.cardId)
    this._clearDropZone()
    body.classList.add("drag-over")
    this._showDropZone(colId, index, this._dragState.cardId)
    return
  }

  _onDragLeave(event) {
    const body = this._bodyFromEvent(event)
    if (body === null) {
      return
    }
    const related = event.relatedTarget
    if (related === null || (related instanceof Node && body.closest(".column").contains(related) === false)) {
      body.classList.remove("drag-over")
    }
    return
  }

  _onDrop(event) {
    const body = this._bodyFromEvent(event)
    if (body === null || this._dragState === null) {
      return
    }
    event.preventDefault()
    const index = this._indexFromPointer(body, event.clientY, this._dragState.cardId)
    const col = this._columnById(body.getAttribute("data-col-id"))
    this._completeDrop(col !== undefined ? col.id : body.getAttribute("data-col-id"), index, false)
    return
  }

  /* ----- touch and pen: pointer events ----- */

  _onPointerDown(event) {
    if (event.pointerType === "mouse" || this._isHandleEvent(event) === false || this._isReadonly() === true) {
      return
    }
    const cardEl = this._cardFromEvent(event)
    const handle = event.target.closest(".card-handle")
    this._pointerDrag = { cardEl: cardEl, handle: handle, startX: event.clientX, startY: event.clientY, started: false, pointerId: event.pointerId }
    if (typeof handle.setPointerCapture === "function" && event.pointerId !== undefined) {
      try {
        handle.setPointerCapture(event.pointerId)
      } catch (error) {
        /* Synthetic events carry no active pointer. */
      }
    }
    return
  }

  /* The column body under a viewport point, if any. */
  _bodyAtPoint(clientX, clientY) {
    let body = null
    const hit = this.shadowRoot.elementFromPoint(clientX, clientY)
    if (hit !== null) {
      const colEl = hit.closest(".column")
      if (colEl !== null) {
        body = colEl.querySelector(".column-body")
      }
    }
    return body
  }

  _onPointerMove(event) {
    const drag = this._pointerDrag
    if (drag === null) {
      return
    }
    if (drag.started === false) {
      const distance = Math.abs(event.clientX - drag.startX) + Math.abs(event.clientY - drag.startY)
      if (distance < TOUCH_DRAG_THRESHOLD) {
        return
      }
      const origin = this._cardOrigin(drag.cardEl)
      if (this._startDrag(origin.cardId, origin.colId, origin.index) === false) {
        this._pointerDrag = null
        return
      }
      drag.started = true
      drag.cardEl.classList.add("dragging")
    }
    event.preventDefault()

    const body = this._bodyAtPoint(event.clientX, event.clientY)
    this._clearDropZone()
    if (body !== null && this._dragState !== null) {
      const colId = body.getAttribute("data-col-id")
      const index = this._indexFromPointer(body, event.clientY, this._dragState.cardId)
      body.classList.add("drag-over")
      this._showDropZone(colId, index, this._dragState.cardId)
      drag.target = { colId: colId, index: index }
    } else {
      drag.target = null
    }
    return
  }

  _onPointerUp(event) {
    const drag = this._pointerDrag
    if (drag === null) {
      return
    }
    this._pointerDrag = null
    if (drag.started === false) {
      return
    }
    drag.cardEl.classList.remove("dragging")
    if (drag.target !== null && drag.target !== undefined && this._dragState !== null) {
      const col = this._columnById(drag.target.colId)
      this._completeDrop(col !== undefined ? col.id : drag.target.colId, drag.target.index, false)
    } else {
      this._cancelDrag()
    }
    return
  }

  _onPointerCancel() {
    const drag = this._pointerDrag
    this._pointerDrag = null
    if (drag !== null && drag.started === true) {
      drag.cardEl.classList.remove("dragging")
      this._cancelDrag()
    }
    return
  }

  /* ----- keyboard move mode ----- */

  _enterMoveMode(cardEl) {
    const origin = this._cardOrigin(cardEl)
    if (this._startDrag(origin.cardId, origin.colId, origin.index) === false) {
      return
    }
    const colIdx = this._columnIndex(origin.colId)
    this._moveMode = {
      cardId: origin.cardId,
      fromColId: origin.colId,
      fromCardIdx: origin.index,
      currentColIdx: colIdx,
      currentCardIdx: origin.index
    }

    cardEl.classList.add("in-move-mode")
    const handle = cardEl.querySelector(".card-handle")
    if (handle !== null) {
      handle.setAttribute("aria-pressed", "true")
    }

    const colEl = cardEl.closest(".column")
    if (colEl !== null) {
      const instr = colEl.querySelector(".move-instructions")
      if (instr !== null) {
        instr.classList.add("visible")
      }
    }

    this._statusRegion.textContent = t("mj.kanban.moveStarted", { title: cardEl.getAttribute("aria-label") })
    this._showDropZone(origin.colId, origin.index, origin.cardId)
    return
  }

  /* Highest position in a column for the moving card. */
  _maxIndexIn(colIdx) {
    const col = this._columns[colIdx]
    let count = this._cardsOf(col).length
    if (col !== undefined && String(col.id) === String(this._moveMode.fromColId)) {
      count = count - 1
    }
    return count
  }

  _onMoveModeKeydown(event) {
    const key = event.key
    const mm = this._moveMode

    if (key === "ArrowLeft" || key === "ArrowRight") {
      event.preventDefault()
      const rtl = window.getComputedStyle(this).direction === "rtl"
      let delta = key === "ArrowRight" ? 1 : -1
      if (rtl === true) {
        delta = -delta
      }
      const newIdx = mm.currentColIdx + delta
      if (newIdx >= 0 && newIdx < this._columns.length) {
        mm.currentColIdx = newIdx
        mm.currentCardIdx = Math.min(mm.currentCardIdx, this._maxIndexIn(newIdx))
      }
    } else if (key === "ArrowUp" || key === "ArrowDown") {
      event.preventDefault()
      const delta = key === "ArrowDown" ? 1 : -1
      mm.currentCardIdx = Math.max(0, Math.min(mm.currentCardIdx + delta, this._maxIndexIn(mm.currentColIdx)))
    } else if (key === "Enter" || key === " ") {
      event.preventDefault()
      event.stopPropagation()
      this._confirmMoveMode()
      return
    } else if (key === "Escape") {
      event.preventDefault()
      event.stopPropagation()
      this._cancelMoveMode()
      return
    } else if (key === "Tab") {
      this._cancelMoveMode()
      return
    } else {
      return
    }

    const col = this._columns[mm.currentColIdx]
    this._clearDropZone()
    this._showDropZone(col.id, mm.currentCardIdx, mm.cardId)
    this._announceTarget(col.id, mm.currentCardIdx)
    return
  }

  _clearMoveModeUI() {
    const cards = this._board.querySelectorAll(".card.in-move-mode")
    for (let i = 0; i < cards.length; i = i + 1) {
      cards[i].classList.remove("in-move-mode")
      const handle = cards[i].querySelector(".card-handle")
      if (handle !== null) {
        handle.setAttribute("aria-pressed", "false")
      }
    }
    this._clearMoveInstructions()
    this._clearDropZone()
    return
  }

  _confirmMoveMode() {
    if (this._moveMode === null) {
      return
    }
    const mm = this._moveMode
    this._moveMode = null
    this._clearMoveModeUI()

    const toCol = this._columns[mm.currentColIdx]
    if (toCol === undefined) {
      this._cancelDrag()
      return
    }
    this._completeDrop(toCol.id, mm.currentCardIdx, true)
    return
  }

  _cancelMoveMode() {
    if (this._moveMode === null) {
      return
    }
    this._moveMode = null
    this._clearMoveModeUI()
    this._cancelDrag()
    this._statusRegion.textContent = t("mj.kanban.moveCanceled")
    return
  }

  /* Leaving the board with focus ends a keyboard move. */
  _onBoardFocusOut(event) {
    if (this._moveMode === null) {
      return
    }
    const next = event.relatedTarget
    if (next === null || (next instanceof Node && this._board.contains(next) === false)) {
      this._cancelMoveMode()
    }
    return
  }

  _clearMoveInstructions() {
    const instrs = this._board.querySelectorAll(".move-instructions")
    for (let i = 0; i < instrs.length; i = i + 1) {
      instrs[i].classList.remove("visible")
    }
    return
  }

  /* ----- scriptable API ----- */

  get columns() {
    return this._columns
  }

  set columns(value) {
    this._columns = Array.isArray(value) === true ? value : []
    if (this._board !== undefined && this._board !== null) {
      this._moveMode = null
      this._dragState = null
      this._renderBoard()
    }
    return
  }

  get dataSource() {
    return this._dataSource
  }

  set dataSource(value) {
    this._dataSource = value !== null && value !== undefined ? value : null
    if (this._board !== undefined && this._board !== null && this._dataSource !== null) {
      this._loadBoard()
    }
    return
  }

  get renderCard() {
    return this._renderCard
  }

  set renderCard(fn) {
    this._renderCard = typeof fn === "function" ? fn : null
    if (this._board !== undefined && this._board !== null) {
      this._renderBoard()
    }
    return
  }

  get loading() {
    return this.hasAttribute("loading")
  }

  set loading(value) {
    this.reflectBoolean("loading", value === true)
    return
  }
}
