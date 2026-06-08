/*
 * mjkanban.js
 *
 * <mj-kanban> -- multi-column card board for workflow visualization.
 * Supports pointer drag-and-drop and full keyboard move interface.
 * WIP limits, live region announcements for screen readers.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

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
  border-bottom: 1px solid var(--mj-border);
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
.wip-badge.exceeded {
  background: var(--mj-color-warning-surface);
  color: var(--mj-color-warning);
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
  border-top: 1px solid var(--mj-border);
}
.move-instructions.visible { display: block; }
`;

export class MjKanban extends MjElement {
  static tagName = "mj-kanban";
  static styles = STYLES;
  static watched = ["mode", "layout", "col-width", "wip-limits", "loading"];

  constructor() {
    super()
    this._columns = []
    this._dataSource = null
    this._renderCard = null
    this._dragState = null
    this._moveMode = null
  }

  render() {
    const markup = `
      <div class="board" part="board" role="application" aria-label="Kanban board"></div>
      <div class="status-region" role="status" aria-live="assertive" aria-atomic="true"></div>
    `
    return markup
  }

  afterRender() {
    this._board = this.$(".board")
    this._statusRegion = this.$(".status-region")

    if (this._columns.length > 0) {
      this._renderBoard()
    }

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
      this._board.setAttribute("aria-busy", newValue !== null ? "true" : "false")
    }
    return
  }

  _loadBoard() {
    if (this._dataSource === null || typeof this._dataSource.fetchBoard !== "function") {
      return
    }
    this.reflectBoolean("loading", true)
    this._dataSource.fetchBoard().then((cols) => {
      this.reflectBoolean("loading", false)
      this._columns = Array.isArray(cols) === true ? cols : []
      this._renderBoard()
      return
    }).catch(() => {
      this.reflectBoolean("loading", false)
    })
    return
  }

  _renderBoard() {
    this._board.innerHTML = ""

    for (let ci = 0; ci < this._columns.length; ci = ci + 1) {
      const col = this._columns[ci]
      const colEl = this._buildColumn(col, ci)
      this._board.appendChild(colEl)
    }
    return
  }

  _buildColumn(col, colIdx) {
    const colEl = document.createElement("section")
    colEl.className = "column"
    colEl.setAttribute("part", "column")
    colEl.setAttribute("role", "group")
    const cardCount = col.cards !== undefined ? col.cards.length : 0
    colEl.setAttribute("aria-label", `${col.label} (${cardCount} cards)`)
    colEl.setAttribute("data-col-id", col.id)

    const header = document.createElement("div")
    header.className = "column-header"
    header.setAttribute("part", "column-header")

    const title = document.createElement("span")
    title.className = "col-title"
    title.textContent = col.label

    header.appendChild(title)

    if (this.hasAttribute("wip-limits") === true && col.wipLimit !== undefined) {
      const badge = document.createElement("span")
      badge.className = cardCount >= col.wipLimit ? "wip-badge exceeded" : "wip-badge"
      badge.setAttribute("aria-label", `${cardCount} of ${col.wipLimit} WIP limit${cardCount >= col.wipLimit ? " — exceeded" : ""}`)
      badge.textContent = `${cardCount}/${col.wipLimit}`
      header.appendChild(badge)
    }

    colEl.appendChild(header)

    const instructions = document.createElement("div")
    instructions.className = "move-instructions"
    instructions.textContent = "Arrow keys to move, Enter to confirm, Escape to cancel."
    colEl.appendChild(instructions)

    const body = document.createElement("div")
    body.className = "column-body"
    body.setAttribute("part", "column-body")
    body.setAttribute("role", "list")
    body.setAttribute("aria-label", col.label)
    body.setAttribute("data-col-id", col.id)
    colEl.appendChild(body)

    this.listen(body, "dragover", (e) => {
      e.preventDefault()
      body.classList.add("drag-over")
    })
    this.listen(body, "dragleave", () => {
      body.classList.remove("drag-over")
    })
    this.listen(body, "drop", (e) => {
      e.preventDefault()
      body.classList.remove("drag-over")
      if (this._dragState !== null) {
        this._completeDrop(col.id, col.cards !== undefined ? col.cards.length : 0)
      }
    })

    const cards = col.cards !== undefined ? col.cards : []

    if (cards.length === 0) {
      const emptySlot = document.createElement("slot")
      emptySlot.setAttribute("name", `empty-${col.id}`)
      body.appendChild(emptySlot)
    }

    for (let ki = 0; ki < cards.length; ki = ki + 1) {
      const card = cards[ki]
      const cardEl = this._buildCard(card, col.id, ki)
      body.appendChild(cardEl)
    }

    return colEl
  }

  _buildCard(card, colId, cardIdx) {
    const cardEl = document.createElement("div")
    cardEl.className = "card"
    cardEl.setAttribute("part", "card")
    cardEl.setAttribute("role", "listitem")
    cardEl.setAttribute("data-card-id", card.id)
    cardEl.setAttribute("data-col-id", colId)
    cardEl.setAttribute("tabindex", "0")
    cardEl.setAttribute("aria-label", card.title || card.id)

    const mode = this.getAttribute("mode") || "interactive"

    if (mode !== "readonly") {
      const handle = document.createElement("button")
      handle.className = "card-handle"
      handle.setAttribute("part", "card-handle")
      handle.setAttribute("aria-label", `Move card: ${card.title || card.id}`)
      handle.setAttribute("aria-pressed", "false")
      handle.textContent = "⠿"
      handle.setAttribute("draggable", "true")

      this.listen(handle, "dragstart", () => {
        this._startDrag(card.id, colId, cardIdx)
        cardEl.classList.add("dragging")
      })
      this.listen(handle, "dragend", () => {
        cardEl.classList.remove("dragging")
        if (this._dragState !== null && this._dragState.completed === false) {
          this._cancelDrag()
        }
      })

      this.listen(handle, "click", (e) => {
        e.stopPropagation()
      })
      this.listen(handle, "keydown", (e) => {
        if (e.key === " " || e.key === "Enter") {
          e.preventDefault()
          this._enterMoveMode(card.id, colId, cardIdx, cardEl, handle)
        }
      })

      cardEl.appendChild(handle)
    }

    const content = document.createElement("div")
    content.className = "card-content"

    if (this._renderCard !== null) {
      const rendered = this._renderCard(card)
      if (typeof rendered === "string") {
        content.innerHTML = rendered
      } else if (rendered instanceof HTMLElement) {
        content.appendChild(rendered)
      }
    } else {
      const titleEl = document.createElement("div")
      titleEl.className = "card-title"
      titleEl.textContent = card.title || card.id
      titleEl.setAttribute("title", card.title || card.id)
      content.appendChild(titleEl)
    }

    cardEl.appendChild(content)

    this.listen(cardEl, "click", () => {
      this.emit("mj-card-click", { cardId: card.id, colId: colId })
    })

    return cardEl
  }

  _startDrag(cardId, fromColId, fromIndex) {
    this._dragState = {
      cardId: cardId,
      fromColId: fromColId,
      fromIndex: fromIndex,
      completed: false
    }
    this.emit("mj-card-move-start", { cardId: cardId, fromColId: fromColId, fromIndex: fromIndex })
    return
  }

  _cancelDrag() {
    this._dragState = null
    return
  }

  _completeDrop(toColId, toIndex) {
    if (this._dragState === null) {
      return
    }
    const ds = this._dragState
    ds.completed = true

    if (ds.fromColId === toColId && ds.fromIndex === toIndex) {
      this._dragState = null
      return
    }

    const proceed = this.emit("mj-card-move", {
      cardId: ds.cardId,
      fromColId: ds.fromColId,
      toColId: toColId,
      toIndex: toIndex
    }, { cancelable: true })

    if (proceed === false) {
      this._dragState = null
      return
    }

    this._moveCardInData(ds.cardId, ds.fromColId, toColId, toIndex)
    this._renderBoard()

    if (this._dataSource !== null && typeof this._dataSource.moveCard === "function") {
      this._dataSource.moveCard(ds.cardId, toColId, toIndex).then(() => {
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

    const toCol = this._columns.find((c) => c.id === toColId)
    if (toCol !== undefined && toCol.wipLimit !== undefined) {
      const count = toCol.cards !== undefined ? toCol.cards.length : 0
      if (count >= toCol.wipLimit) {
        this.emit("mj-col-wip-exceeded", { colId: toColId, count: count, limit: toCol.wipLimit })
      }
    }

    this._dragState = null
    return
  }

  _moveCardInData(cardId, fromColId, toColId, toIndex) {
    const fromCol = this._columns.find((c) => c.id === fromColId)
    const toCol = this._columns.find((c) => c.id === toColId)
    if (fromCol === undefined || toCol === undefined) {
      return
    }

    const fromCards = fromCol.cards !== undefined ? fromCol.cards : []
    const cardIdx = fromCards.findIndex((c) => c.id === cardId)
    if (cardIdx < 0) {
      return
    }

    const card = fromCards[cardIdx]
    fromCol.cards = fromCards.filter((c) => c.id !== cardId)

    const toCards = toCol.cards !== undefined ? toCol.cards : []
    const insertAt = Math.min(toIndex, toCards.length)
    toCards.splice(insertAt, 0, card)
    toCol.cards = toCards
    return
  }

  _enterMoveMode(cardId, colId, cardIdx, cardEl, handleBtn) {
    const colIdx = this._columns.findIndex((c) => c.id === colId)
    this._moveMode = {
      cardId: cardId,
      fromColId: colId,
      fromCardIdx: cardIdx,
      currentColIdx: colIdx,
      currentCardIdx: cardIdx
    }

    cardEl.classList.add("in-move-mode")
    handleBtn.setAttribute("aria-pressed", "true")

    const colEl = this._board.querySelector(`[data-col-id="${colId}"]`)
    if (colEl !== null) {
      const instr = colEl.querySelector(".move-instructions")
      if (instr !== null) {
        instr.classList.add("visible")
      }
    }

    this._statusRegion.textContent = `Moving card: ${cardEl.getAttribute("aria-label")}. Use arrow keys to reposition.`

    const onKey = (e) => {
      if (this._moveMode === null) {
        document.removeEventListener("keydown", onKey)
        return
      }
      if (e.key === "ArrowLeft") {
        e.preventDefault()
        this._moveModeColumn(-1)
      } else if (e.key === "ArrowRight") {
        e.preventDefault()
        this._moveModeColumn(1)
      } else if (e.key === "ArrowUp") {
        e.preventDefault()
        this._moveModeRow(-1)
      } else if (e.key === "ArrowDown") {
        e.preventDefault()
        this._moveModeRow(1)
      } else if (e.key === "Enter") {
        e.preventDefault()
        document.removeEventListener("keydown", onKey)
        this._confirmMoveMode(cardEl, handleBtn)
      } else if (e.key === "Escape") {
        e.preventDefault()
        document.removeEventListener("keydown", onKey)
        this._cancelMoveMode(cardEl, handleBtn)
      }
    }

    document.addEventListener("keydown", onKey)
    this.onTeardown(() => { document.removeEventListener("keydown", onKey) })
    return
  }

  _moveModeColumn(delta) {
    if (this._moveMode === null) {
      return
    }
    const newIdx = this._moveMode.currentColIdx + delta
    if (newIdx < 0 || newIdx >= this._columns.length) {
      return
    }
    this._moveMode.currentColIdx = newIdx
    const col = this._columns[newIdx]
    const cardCount = col.cards !== undefined ? col.cards.length : 0
    this._moveMode.currentCardIdx = cardCount
    this._statusRegion.textContent = `Moving to column: ${col.label}, position ${cardCount + 1}.`
    return
  }

  _moveModeRow(delta) {
    if (this._moveMode === null) {
      return
    }
    const col = this._columns[this._moveMode.currentColIdx]
    const cardCount = col.cards !== undefined ? col.cards.length : 0
    const newIdx = Math.max(0, Math.min(this._moveMode.currentCardIdx + delta, cardCount))
    this._moveMode.currentCardIdx = newIdx
    this._statusRegion.textContent = `Position ${newIdx + 1} in column ${col.label}.`
    return
  }

  _confirmMoveMode(cardEl, handleBtn) {
    if (this._moveMode === null) {
      return
    }
    const mm = this._moveMode
    cardEl.classList.remove("in-move-mode")
    handleBtn.setAttribute("aria-pressed", "false")
    this._clearMoveInstructions()
    this._moveMode = null

    const toCol = this._columns[mm.currentColIdx]
    if (toCol === undefined) {
      return
    }

    this._startDrag(mm.cardId, mm.fromColId, mm.fromCardIdx)
    this._completeDrop(toCol.id, mm.currentCardIdx)

    this._statusRegion.textContent = `Card moved to ${toCol.label}.`
    return
  }

  _cancelMoveMode(cardEl, handleBtn) {
    cardEl.classList.remove("in-move-mode")
    handleBtn.setAttribute("aria-pressed", "false")
    this._clearMoveInstructions()
    this._moveMode = null
    this._statusRegion.textContent = "Move canceled."
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
