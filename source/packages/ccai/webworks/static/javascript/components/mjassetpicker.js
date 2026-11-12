/*
 * mjassetpicker.js
 *
 * <mj-asset-picker> — searchable, categorized grid picker for emoji, icons,
 * fonts, or author-supplied visual assets. Form-associated.
 *
 * An asset is `{ id, label, category?, keywords?, glyph?, src? }`. The cell
 * shows `src` as an image when present, otherwise `glyph`, otherwise `id`
 * (for an emoji the id is the character itself).
 *
 * Where the assets come from:
 *   assets       property: an array of assets
 *   dataSource   property: an array, an object with `query(request)` (the
 *                core DataSource contract) or an object with `search(text)`;
 *                results may be returned directly or as a Promise
 *   type="emoji" a built-in starter set of common emoji, used when neither
 *                property is set. It is not the full Unicode list; supply
 *                `assets` for a complete one.
 *
 * State lives in fields (`_assets`, `_selectedIds`, `_activeCategory`,
 * `_query`, `_activeId`) and the popup is painted from them. The `value`
 * attribute is the INITIAL selection; picking an asset updates the `value`
 * property and the form value but is not written back to the attribute.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { autoPosition } from "../core/overlay.js";
import { trapFocus } from "../core/focustrap.js";
import { announce } from "../core/announcer.js";
import { html, safeUrl } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: inline-block; vertical-align: middle; }

.trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: var(--mj-control-height-md);
  min-height: var(--mj-control-height-md);
  padding: 0 var(--mj-space-3);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  background: var(--mj-surface);
  cursor: pointer;
  font: inherit;
  color: var(--mj-text);
  gap: var(--mj-space-2);
}
.trigger:hover { background: var(--mj-bg-muted); }
.trigger:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
:host([disabled]) .trigger,
:host(:disabled) .trigger { opacity: 0.55; cursor: not-allowed; pointer-events: none; }

/*
 * By default the popup is as wide as its content: the category column plus
 * the asset grid (columns x cell size), its padding and a reserved scrollbar
 * gutter, so every column fits whatever the columns / cell-size attributes say.
 */
.popup {
  position: fixed;
  width: var(--mj-asset-picker-popup-width, max-content);
  max-width: calc(100vw - 2 * var(--mj-space-2));
  height: var(--mj-asset-picker-popup-height, 24rem);
  background: var(--mj-surface-raised, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-3);
  z-index: var(--mj-layer-popover);
  display: none;
  flex-direction: column;
}
:host([open]) .popup { display: flex; }

.search-wrapper {
  padding: var(--mj-space-2) var(--mj-space-3);
  border-block-end: 1px solid var(--mj-border);
  flex-shrink: 0;
}
.search-input {
  width: 100%;
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-sm);
  padding: var(--mj-space-1) var(--mj-space-2);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  background: var(--mj-surface);
}
.search-input:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }

.body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.category-nav {
  width: var(--mj-asset-picker-category-width, 3rem);
  border-inline-end: 1px solid var(--mj-border);
  overflow-y: auto;
  flex-shrink: 0;
  padding: var(--mj-space-1) 0;
}
.category-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: var(--mj-asset-picker-cell-size, 2rem);
  padding: var(--mj-space-1);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  border-radius: 0;
}
.category-btn:hover, .category-btn[aria-pressed="true"] { background: var(--mj-bg-muted); }
.category-btn[aria-pressed="true"] { box-shadow: inset 0 -2px 0 var(--mj-accent); }
.category-btn:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: -2px; }

.asset-area {
  flex: 1;
  overflow-y: auto;
  scrollbar-gutter: stable;
  padding: var(--mj-space-2);
}
/* The no-results text fills the area but never widens the popup. */
.no-results {
  inline-size: 0;
  min-inline-size: 100%;
  box-sizing: border-box;
}
/*
 * Each role="row" is its own grid track, so assets flow across and wrap
 * exactly where the arrow-key maths expects. --cols and --cell are set from
 * the columns / cell-size attributes.
 */
.asset-row {
  display: grid;
  grid-template-columns: repeat(var(--cols, 8), var(--cell, var(--mj-asset-picker-cell-size, 2rem)));
  gap: 2px;
  margin-block-end: 2px;
}
.asset-cell {
  width: var(--cell, var(--mj-asset-picker-cell-size, 2rem));
  height: var(--cell, var(--mj-asset-picker-cell-size, 2rem));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--mj-asset-picker-font-size, 1.25rem);
  border-radius: var(--mj-asset-picker-cell-radius, var(--mj-radius-sm));
  cursor: pointer;
  border: 2px solid transparent;
  background: none;
  padding: 0;
}
.asset-cell:hover { background: var(--mj-bg-muted); }
.asset-cell:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.asset-cell.selected {
  background: var(--mj-asset-picker-selected-bg, var(--mj-bg-subtle));
  border-color: var(--mj-accent);
}
.asset-cell img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
.trigger-value img {
  width: 1.25em;
  height: 1.25em;
  object-fit: contain;
  vertical-align: middle;
}

.no-results {
  padding: var(--mj-space-4);
  text-align: center;
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
}

.section-label {
  font-size: var(--mj-font-size-xs);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: var(--mj-space-1) 0;
  margin-block-end: var(--mj-space-1);
}
`;

/*
 * Built-in starter emoji, by category. Each entry is "<emoji> <name>"; the
 * emoji is the asset id and the name is its accessible label. This is a
 * selection of common emoji, not the full Unicode set.
 */
const BUILTIN_EMOJI_GROUPS = [
  ["Smileys", "😀 grinning face|😃 grinning face with big eyes|😄 grinning face with smiling eyes|😁 beaming face with smiling eyes|😆 grinning squinting face|😅 grinning face with sweat|🤣 rolling on the floor laughing|😂 face with tears of joy|🙂 slightly smiling face|🙃 upside-down face|😉 winking face|😊 smiling face with smiling eyes|😇 smiling face with halo|🥰 smiling face with hearts|😍 smiling face with heart-eyes|😘 face blowing a kiss|😋 face savoring food|😎 smiling face with sunglasses|🤔 thinking face|😐 neutral face|😴 sleeping face|😢 crying face|😭 loudly crying face|😡 enraged face|😱 face screaming in fear|🤯 exploding head|🥳 partying face|😷 face with medical mask"],
  ["People", "👍 thumbs up|👎 thumbs down|👏 clapping hands|🙌 raising hands|👋 waving hand|🤝 handshake|🙏 folded hands|💪 flexed biceps|👀 eyes|👌 OK hand|✌️ victory hand|🤞 crossed fingers|👉 backhand index pointing right|👈 backhand index pointing left|👆 backhand index pointing up|👇 backhand index pointing down|✋ raised hand|🤷 person shrugging|🙋 person raising hand|👶 baby|👪 family|🧠 brain|👤 bust in silhouette"],
  ["Animals", "🐶 dog face|🐱 cat face|🐭 mouse face|🐰 rabbit face|🦊 fox|🐻 bear|🐼 panda|🐨 koala|🐯 tiger face|🦁 lion|🐮 cow face|🐷 pig face|🐸 frog|🐵 monkey face|🐔 chicken|🐧 penguin|🐦 bird|🦄 unicorn|🐝 honeybee|🦋 butterfly|🐢 turtle|🐍 snake|🐬 dolphin|🐳 spouting whale|🌸 cherry blossom|🌹 rose|🌻 sunflower|🌲 evergreen tree|🌵 cactus|🍀 four leaf clover"],
  ["Food", "🍎 red apple|🍊 tangerine|🍋 lemon|🍌 banana|🍉 watermelon|🍇 grapes|🍓 strawberry|🍒 cherries|🍑 peach|🍍 pineapple|🥑 avocado|🍅 tomato|🥕 carrot|🌽 ear of corn|🍞 bread|🧀 cheese wedge|🍔 hamburger|🍟 french fries|🍕 pizza|🌮 taco|🍣 sushi|🍜 steaming bowl|🍰 shortcake|🍪 cookie|🍫 chocolate bar|🍩 doughnut|☕ hot beverage|🍵 teacup without handle|🍺 beer mug|🍷 wine glass"],
  ["Travel", "🚗 automobile|🚕 taxi|🚌 bus|🚲 bicycle|🚂 locomotive|✈️ airplane|🚀 rocket|🚁 helicopter|⛵ sailboat|🚢 ship|🏠 house|🏢 office building|🏥 hospital|🏫 school|🏰 castle|🗽 Statue of Liberty|🌍 globe showing Europe-Africa|🌎 globe showing Americas|🌏 globe showing Asia-Australia|🌋 volcano|☀️ sun|🌙 crescent moon|⭐ star|🌟 glowing star|☁️ cloud|⚡ high voltage|🔥 fire|🌈 rainbow|❄️ snowflake"],
  ["Activities", "🎉 party popper|🎊 confetti ball|🎈 balloon|🎁 wrapped gift|🏆 trophy|🥇 1st place medal|⚽ soccer ball|🏀 basketball|🏈 american football|⚾ baseball|🎾 tennis|🏐 volleyball|🎱 pool 8 ball|🏓 ping pong|🎯 bullseye|🎮 video game|🎲 game die|🧩 puzzle piece|🎨 artist palette|🎭 performing arts|🎬 clapper board|🎤 microphone|🎧 headphone|🎸 guitar|🎹 musical keyboard|🎵 musical note"],
  ["Objects", "💡 light bulb|📱 mobile phone|💻 laptop|⌨️ keyboard|📷 camera|📺 television|⏰ alarm clock|⌛ hourglass done|🔋 battery|🔌 electric plug|🔑 key|🔒 locked|🔓 unlocked|🔨 hammer|🔧 wrench|⚙️ gear|🧰 toolbox|📦 package|📁 file folder|📂 open file folder|📄 page facing up|📝 memo|📌 pushpin|📎 paperclip|✏️ pencil|📚 books|📅 calendar|📈 chart increasing|📉 chart decreasing|📊 bar chart|✉️ envelope|📧 e-mail|🔔 bell|🔍 magnifying glass tilted left|💰 money bag|🛒 shopping cart"],
  ["Symbols", "❤️ red heart|🧡 orange heart|💛 yellow heart|💚 green heart|💙 blue heart|💜 purple heart|🖤 black heart|💔 broken heart|💯 hundred points|✅ check mark button|❌ cross mark|⚠️ warning|❓ red question mark|❗ red exclamation mark|➕ plus|➖ minus|♻️ recycling symbol|🚫 prohibited|🆗 OK button|🆕 NEW button|🔴 red circle|🟢 green circle|🔵 blue circle|⬆️ up arrow|⬇️ down arrow|➡️ right arrow|⬅️ left arrow|🔄 counterclockwise arrows button|✨ sparkles|💬 speech balloon|💤 zzz"]
];

function buildBuiltinEmoji() {
  const assets = []
  for (let groupIndex = 0; groupIndex < BUILTIN_EMOJI_GROUPS.length; groupIndex = groupIndex + 1) {
    const category = BUILTIN_EMOJI_GROUPS[groupIndex][0]
    const entries = BUILTIN_EMOJI_GROUPS[groupIndex][1].split("|")
    for (let index = 0; index < entries.length; index = index + 1) {
      const entry = entries[index]
      const space = entry.indexOf(" ")
      assets.push({ id: entry.slice(0, space), label: entry.slice(space + 1), category: category })
    }
  }
  return assets
}

const TRIGGER_PLACEHOLDER = "☺";
const MAX_COLUMNS = 24;

export class MjAssetPicker extends FormControlMixin(MjElement) {
  static tagName = "mj-asset-picker";
  static styles = STYLES;
  static watched = [
    "name", "value", "open", "disabled", "required", "type", "columns",
    "cell-size", "multiple", "search-placeholder"
  ];

  constructor() {
    super()
    this._initFormControl()

    this._selectedIds = new Set()

    /* All assets, and the ones the category / search currently shows. */
    this._assets = []
    this._filteredAssets = []

    /* True when `assets` or `dataSource` supplied the assets. */
    this._assetsSupplied = false
    this._dataSource = null
    this._loadSeq = 0

    /* null shows every category. */
    this._activeCategory = null
    this._query = ""

    /* The asset whose cell holds the grid's single tab stop. */
    this._activeId = null

    this._disposePosition = null
    this._disposeTrap = null
    this._searchTimer = null
    this._recentAssets = []
    this._triggerId = nextId("mj-ap-tr")
    this._popupId = nextId("mj-ap-popup")
    this._gridId = nextId("mj-ap-grid")

    /* True when the `value` attribute was applied before the first render. */
    this._valueReplayPending = false

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    this._trigger = null
    this._popup = null
  }

  render() {
    const markup = html`
      <button
        class="trigger"
        part="trigger"
        id="${this._triggerId}"
        type="button"
        aria-haspopup="dialog"
        aria-expanded="false"
        aria-controls="${this._popupId}"
        aria-label="${t("mj.assetPicker.triggerLabel")}"
      >
        <slot name="trigger">
          <span class="trigger-value"></span>
        </slot>
      </button>
      <div class="popup" part="popup" id="${this._popupId}" role="dialog" aria-label="${t("mj.assetPicker.dialogLabel")}">
        <div class="search-wrapper">
          <input
            class="search-input"
            part="search"
            type="text"
            aria-label="${t("mj.assetPicker.searchLabel")}"
            autocomplete="off"
          />
        </div>
        <div class="body">
          <div class="category-nav" part="category-nav" role="group" aria-label="${t("mj.assetPicker.categoriesLabel")}"></div>
          <div class="asset-area" part="asset-area">
            <div
              class="asset-grid"
              part="asset-grid"
              id="${this._gridId}"
              role="grid"
              aria-label="${t("mj.assetPicker.gridLabel")}"
            ></div>
            <div class="no-results" part="no-results" hidden><slot name="no-results">${t("core.noResults")}</slot></div>
          </div>
        </div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._trigger = this.$(".trigger")
    this._triggerValue = this.$(".trigger-value")
    this._popup = this.$(".popup")
    this._searchInput = this.$(".search-input")
    this._categoryNav = this.$(".category-nav")
    this._assetGrid = this.$(".asset-grid")
    this._assetArea = this.$(".asset-area")
    this._noResults = this.$(".no-results")

    /* One listener each; the cells and category buttons are rebuilt often. */
    this.listen(this._trigger, "click", this._onTriggerClick.bind(this))
    this.listen(this._searchInput, "input", this._onSearch.bind(this))
    this.listen(this._categoryNav, "click", this._onCategoryClick.bind(this))
    this.listen(this._assetGrid, "click", this._onAssetClick.bind(this))
    this.listen(this._assetGrid, "keydown", this._onGridKeydown.bind(this))
    this.listen(this._popup, "keydown", this._onPopupKeydown.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))
    this.onTeardown(() => {
      clearTimeout(this._searchTimer)
      this._searchTimer = null
    })

    if (this._assetsSupplied === false) {
      this._loadBuiltinAssets()
    }

    /* Everything below paints the fresh shadow DOM from the fields. */
    this._searchInput.value = this._query
    this._searchInput.placeholder = this.getAttribute("search-placeholder") || t("core.search")
    this._syncDisabled()
    this._updateGridStyle()
    this._applyFilter()
    this._renderCategories()
    this._updateTrigger()
    this._setFormValue(this._value || "")
    this._syncOpen()
    return
  }

  onDisconnected() {
    /* A removed picker must not keep tracking scroll/resize or trapping Tab. */
    this._releaseOverlay()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      if (this._rendered === false) {
        this._valueReplayPending = true
        this._applyValue(newValue || "")
      } else if (this._valueReplayPending === true) {
        /* The same change was applied before the first render. */
        this._valueReplayPending = false
      } else {
        this._applyValue(newValue || "")
      }
    }
    if (name === "multiple") {
      /* Leaving multiple mode keeps the first selected asset only. */
      this._applyValue(this._value || "")
    }
    if (name === "open") {
      this._syncOpen()
    }
    if (name === "columns" || name === "cell-size") {
      this._updateGridStyle()
      this._renderGrid()
    }
    if (name === "type" && this._assetsSupplied === false && this._rendered === true) {
      this._loadBuiltinAssets()
      this._activeCategory = null
      this._applyFilter()
      this._renderCategories()
      this._updateTrigger()
    }
    if (name === "disabled") {
      this._syncDisabled()
    }
    if (name === "required" && this._internals !== undefined) {
      this._refreshValidity()
    }
    if (name === "search-placeholder" && this._searchInput !== undefined) {
      this._searchInput.placeholder = newValue || t("core.search")
    }
    return
  }

  onFormReset(initial) {
    this._applyValue(initial)
    return
  }

  onFormRestore(state) {
    if (typeof state === "string") {
      this._applyValue(state)
    }
    return
  }

  /* An ancestor <fieldset disabled> was switched on or off. */
  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    this._syncDisabled()
    return
  }

  _validationAnchor() {
    return this._trigger
  }

  /* Disabled by its own attribute or by an ancestor <fieldset disabled>. */
  _isDisabled() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    return disabled
  }

  /* Mirror the disabled state onto the trigger; a disabled picker cannot stay open. */
  _syncDisabled() {
    if (this._trigger === undefined || this._trigger === null) {
      return
    }
    const disabled = this._isDisabled()
    this._trigger.disabled = disabled
    if (disabled === true && this.hasAttribute("open") === true) {
      this._close()
    }
    return
  }

  /* ----- assets ----- */

  _loadBuiltinAssets() {
    const type = this.getAttribute("type") || "emoji"
    this._assets = type === "emoji" ? buildBuiltinEmoji() : []
    return
  }

  /* Keep only well-formed assets; ids and labels are compared and shown as strings. */
  _normalizeAssets(list) {
    const assets = []
    const entries = Array.isArray(list) === true ? list : []

    for (let index = 0; index < entries.length; index = index + 1) {
      const entry = entries[index]
      if (entry !== null && typeof entry === "object" && entry.id !== null && entry.id !== undefined) {
        const id = String(entry.id)
        const asset = Object.assign({}, entry, {
          id: id,
          label: entry.label !== null && entry.label !== undefined ? String(entry.label) : id
        })
        assets.push(asset)
      } else if (typeof entry === "string" && entry.length > 0) {
        assets.push({ id: entry, label: entry })
      }
    }

    return assets
  }

  /* Replace the asset list and repaint everything that depends on it. */
  _setAssets(list) {
    this._assets = this._normalizeAssets(list)
    this._assetsSupplied = true

    const categories = this._getCategories()
    if (this._activeCategory !== null && categories.indexOf(this._activeCategory) < 0) {
      this._activeCategory = null
    }

    if (this._assetGrid !== undefined && this._assetGrid !== null) {
      this._applyFilter()
      this._renderCategories()
      this._updateTrigger()
    }
    return
  }

  /* Read every asset from the data source (array, `query()` or `search()`). */
  async _loadFromDataSource() {
    const source = this._dataSource
    this._loadSeq = this._loadSeq + 1
    const loadSeq = this._loadSeq

    let result = []
    try {
      if (Array.isArray(source) === true) {
        result = source
      } else if (source !== null && typeof source.query === "function") {
        result = await source.query({ offset: 0, limit: 10000, filter: "" })
      } else if (source !== null && typeof source.search === "function") {
        result = await source.search("")
      }
    } catch (error) {
      console.error("mj-asset-picker: the data source failed to load", error)
      result = []
    }

    /* A newer assignment superseded this one. */
    if (loadSeq !== this._loadSeq) {
      return
    }

    let items = []
    if (Array.isArray(result) === true) {
      items = result
    } else if (result !== null && result !== undefined && Array.isArray(result.items) === true) {
      items = result.items
    }
    this._setAssets(items)
    return
  }

  _updateGridStyle() {
    if (this._assetGrid === undefined || this._assetGrid === null) {
      return
    }
    this._assetGrid.style.setProperty("--cols", String(this._columns()))

    const cellSize = this.getAttribute("cell-size") || ""
    if (cellSize.length > 0) {
      /* setProperty takes one value: a malformed size is simply not applied. */
      this._assetGrid.style.setProperty("--cell", cellSize)
    } else {
      this._assetGrid.style.removeProperty("--cell")
    }
    return
  }

  _columns() {
    const parsed = parseInt(this.getAttribute("columns") || "8", 10)
    let columns = 8
    if (Number.isNaN(parsed) === false && parsed >= 1) {
      columns = Math.min(parsed, MAX_COLUMNS)
    }
    return columns
  }

  _getCategories() {
    const cats = new Set()
    this._assets.forEach((a) => {
      if (a.category !== undefined && a.category !== null && a.category !== "") {
        cats.add(String(a.category))
      }
    })
    return Array.from(cats)
  }

  /* The markup that shows an asset: its image, else its glyph, else its id. */
  _assetVisual(asset) {
    let visual = html`${asset.id}`
    if (asset.src !== undefined && asset.src !== null && asset.src !== "") {
      visual = html`<img part="asset-image" src="${safeUrl(asset.src, "")}" alt="" />`
    } else if (asset.glyph !== undefined && asset.glyph !== null && asset.glyph !== "") {
      visual = html`${asset.glyph}`
    }
    return visual
  }

  /* Category buttons are toggles: the pressed one filters the grid. */
  _renderCategories() {
    const cats = this._getCategories()
    this._categoryNav.hidden = cats.length === 0
    if (cats.length === 0) {
      this._categoryNav.textContent = ""
      return
    }

    const buttons = [html`<button
      class="category-btn"
      part="category-button"
      type="button"
      aria-pressed="${this._activeCategory === null ? "true" : "false"}"
      aria-label="${t("mj.assetPicker.allCategories")}"
      title="${t("mj.assetPicker.allCategories")}"
      data-all="true"
    >&#10033;</button>`]

    cats.forEach((cat) => {
      const first = this._assets.find((a) => String(a.category) === cat)
      buttons.push(html`<button
        class="category-btn"
        part="category-button"
        type="button"
        aria-pressed="${this._activeCategory === cat ? "true" : "false"}"
        aria-label="${cat}"
        title="${cat}"
        data-category="${cat}"
      >${first !== undefined ? this._assetVisual(first) : cat.slice(0, 1)}</button>`)
    })

    this._categoryNav.innerHTML = String(html`${buttons}`)
    return
  }

  _onCategoryClick(event) {
    const btn = event.target.closest(".category-btn")
    if (btn === null) {
      return
    }
    this._activeCategory = btn.dataset.all === "true" ? null : btn.dataset.category

    /* Choosing a category leaves search mode. */
    this._query = ""
    this._searchInput.value = ""

    const buttons = this._categoryNav.querySelectorAll(".category-btn")
    buttons.forEach((candidate) => {
      candidate.setAttribute("aria-pressed", candidate === btn ? "true" : "false")
    })
    this._applyFilter()
    return
  }

  /* Work out which assets are shown (search wins over category) and paint them. */
  _applyFilter() {
    const query = this._query

    if (query.length > 0) {
      this._filteredAssets = this._assets.filter((a) => {
        const keywords = Array.isArray(a.keywords) === true ? a.keywords.join(" ") : ""
        const haystack = `${a.label} ${a.id} ${keywords}`.toLowerCase()
        return haystack.includes(query)
      })
    } else if (this._activeCategory !== null) {
      this._filteredAssets = this._assets.filter((a) => String(a.category) === this._activeCategory)
    } else {
      this._filteredAssets = this._assets.slice()
    }

    this._renderGrid()
    return
  }

  _renderGrid() {
    if (this._assetGrid === undefined || this._assetGrid === null) {
      return
    }
    const assets = this._filteredAssets
    this._noResults.hidden = assets.length > 0
    this._assetGrid.hidden = assets.length === 0

    /* Rebuilding the cells destroys the focused one; remember to restore it. */
    const hadFocus = this._assetGrid.contains(this.shadowRoot.activeElement)

    /* The tab stop stays on a shown asset: the active one, a selected one, else the first. */
    const shown = (id) => assets.some((a) => a.id === id)
    if (this._activeId === null || shown(this._activeId) === false) {
      const firstSelected = assets.find((a) => this._selectedIds.has(a.id))
      if (firstSelected !== undefined) {
        this._activeId = firstSelected.id
      } else {
        this._activeId = assets.length > 0 ? assets[0].id : null
      }
    }

    const cols = this._columns()
    const rows = []
    for (let start = 0; start < assets.length; start = start + cols) {
      const cells = assets.slice(start, start + cols).map((asset) => {
        const cell = html`<div role="gridcell" aria-selected="false">
          <button
            class="asset-cell"
            part="asset-cell"
            type="button"
            aria-label="${asset.label}"
            aria-pressed="false"
            title="${asset.label}"
            data-id="${asset.id}"
            tabindex="-1"
          >${this._assetVisual(asset)}</button>
        </div>`
        return cell
      })
      rows.push(html`<div class="asset-row" role="row">${cells}</div>`)
    }

    this._assetGrid.innerHTML = String(html`${rows}`)
    this._assetGrid.setAttribute("aria-rowcount", String(rows.length))
    this._assetGrid.setAttribute("aria-colcount", String(cols))
    this._refreshCells()

    if (hadFocus === true) {
      const stop = this._assetGrid.querySelector(".asset-cell[tabindex='0']")
      if (stop !== null) {
        stop.focus()
      }
    }
    return
  }

  /*
   * Mark the selected cells and the tab stop on the rendered grid, in place.
   * A selection change goes through here, so the clicked cell keeps focus.
   */
  _refreshCells() {
    const cells = this._assetGrid.querySelectorAll(".asset-cell")
    cells.forEach((cell) => {
      const id = cell.dataset.id
      const selected = this._selectedIds.has(id)
      cell.classList.toggle("selected", selected)
      cell.setAttribute("aria-pressed", selected === true ? "true" : "false")
      cell.parentElement.setAttribute("aria-selected", selected === true ? "true" : "false")
      cell.tabIndex = id === this._activeId ? 0 : -1
    })
    return
  }

  _onSearch() {
    clearTimeout(this._searchTimer)
    this._searchTimer = setTimeout(() => {
      this._searchTimer = null
      this._runSearch()
    }, 150)
    return
  }

  async _runSearch() {
    const query = this._searchInput.value.toLowerCase().trim()
    this._query = query

    const source = this._dataSource
    const remote = query.length > 0 && source !== null && Array.isArray(source) === false &&
      typeof source.search === "function"

    if (remote === true) {
      /* The data source knows how to search itself. */
      let found = []
      try {
        found = await source.search(query)
      } catch (error) {
        found = []
      }
      if (this._query !== query) {
        return
      }
      this._filteredAssets = this._normalizeAssets(Array.isArray(found) === true ? found : (found !== null && found !== undefined ? found.items : []))
      this._renderGrid()
    } else {
      this._applyFilter()
    }

    const count = this._filteredAssets.length
    announce(query.length > 0 ? t("mj.assetPicker.resultsForQuery", { count: count, query: query }) : t("mj.assetPicker.results", { count: count }), "polite")
    this.emit("mj-search", { query: query, results: this._filteredAssets.slice() })
    return
  }

  /* ----- selection ----- */

  _findAsset(id) {
    let asset = this._assets.find((a) => a.id === id)
    if (asset === undefined) {
      asset = this._filteredAssets.find((a) => a.id === id)
    }
    return asset !== undefined ? asset : null
  }

  /*
   * Select the comma-separated ids in `text` (the first one only unless
   * `multiple` is set). No event is emitted.
   */
  _applyValue(text) {
    const ids = String(text || "").split(",").map((id) => id.trim()).filter((id) => id.length > 0)
    const kept = this.hasAttribute("multiple") === true ? ids : ids.slice(0, 1)

    this._selectedIds = new Set(kept)
    this._setFormValue(Array.from(this._selectedIds).join(","))

    if (this._assetGrid !== undefined && this._assetGrid !== null) {
      this._refreshCells()
      this._updateTrigger()
    }
    return
  }

  _onAssetClick(event) {
    const btn = event.target.closest(".asset-cell")
    if (btn === null || this._isDisabled() === true) {
      return
    }
    const id = btn.dataset.id
    const asset = this._findAsset(id)
    const isMultiple = this.hasAttribute("multiple")

    if (isMultiple === false) {
      this._selectedIds.clear()
      this._selectedIds.add(id)
    } else if (this._selectedIds.has(id) === true) {
      this._selectedIds.delete(id)
    } else {
      this._selectedIds.add(id)
    }

    this._activeId = id
    const newValue = Array.from(this._selectedIds).join(",")
    this._setFormValue(newValue)

    /* Updated in place: the clicked cell is still there and keeps focus. */
    this._refreshCells()
    this._updateTrigger()

    if (asset !== null && this._selectedIds.has(id) === true) {
      this._trackRecent(asset)
    }

    this.emit("mj-change", {
      value: newValue,
      asset: asset,
      assets: this.selectedAssets
    })

    if (isMultiple === false) {
      this._close()
    }
    return
  }

  _onGridKeydown(event) {
    const cells = Array.from(this._assetGrid.querySelectorAll(".asset-cell"))
    const count = cells.length
    if (count === 0) {
      return
    }

    const current = cells.findIndex((c) => c === this.shadowRoot.activeElement)
    if (current < 0) {
      return
    }
    const cols = this._columns()
    const rowStart = current - (current % cols)
    const withCtrl = event.ctrlKey === true || event.metaKey === true

    /* Ctrl+Home / Ctrl+End are tested first: plain Home / End would match them too. */
    let next = current
    if (withCtrl === true && event.key === "Home") {
      next = 0
    } else if (withCtrl === true && event.key === "End") {
      next = count - 1
    } else if (event.key === "ArrowRight") {
      next = Math.min(current + 1, count - 1)
    } else if (event.key === "ArrowLeft") {
      next = Math.max(current - 1, 0)
    } else if (event.key === "ArrowDown") {
      next = current + cols < count ? current + cols : current
    } else if (event.key === "ArrowUp") {
      next = current - cols >= 0 ? current - cols : current
    } else if (event.key === "Home") {
      next = rowStart
    } else if (event.key === "End") {
      next = Math.min(rowStart + cols - 1, count - 1)
    } else {
      return
    }

    event.preventDefault()
    this._activeId = cells[next].dataset.id
    this._refreshCells()
    cells[next].focus()
    return
  }

  /* Show what is selected on the trigger and in its accessible name. */
  _updateTrigger() {
    if (this._trigger === undefined || this._trigger === null) {
      return
    }
    const ids = Array.from(this._selectedIds)
    const shownIds = ids.slice(0, 3)
    const labels = []
    const visuals = []

    for (let index = 0; index < ids.length; index = index + 1) {
      const asset = this._findAsset(ids[index])
      labels.push(asset !== null ? asset.label : ids[index])
      if (index < shownIds.length) {
        visuals.push(asset !== null ? this._assetVisual(asset) : html`${ids[index]}`)
      }
    }

    let content = html`${TRIGGER_PLACEHOLDER}`
    if (ids.length > 0) {
      const more = ids.length > shownIds.length ? html` +${ids.length - shownIds.length}` : ""
      content = html`${visuals}${more}`
    }
    this._triggerValue.innerHTML = String(content)

    const label = ids.length > 0 ? t("mj.assetPicker.triggerLabelCurrent", { labels: labels.join(", ") }) : t("mj.assetPicker.triggerLabel")
    this._trigger.setAttribute("aria-label", label)
    return
  }

  _trackRecent(asset) {
    this._recentAssets = this._recentAssets.filter((a) => a.id !== asset.id)
    this._recentAssets.unshift(asset)
    const maxRecents = parseInt(this.getAttribute("recents-count") || "18", 10)
    if (this._recentAssets.length > maxRecents) {
      this._recentAssets = this._recentAssets.slice(0, maxRecents)
    }
    try {
      const key = `mj-asset-picker-recents-${this.getAttribute("type") || "emoji"}`
      localStorage.setItem(key, JSON.stringify(this._recentAssets.map((a) => a.id)))
    } catch {
      /* localStorage unavailable */
    }
    return
  }

  /* ----- open / close ----- */

  /* Stop tracking the popup position and release the focus trap. */
  _releaseOverlay() {
    if (this._disposePosition !== null) {
      this._disposePosition()
      this._disposePosition = null
    }
    if (this._disposeTrap !== null) {
      /* Where focus goes on close is decided by `_syncOpen`, not by the trap. */
      this._disposeTrap({ restoreFocus: false })
      this._disposeTrap = null
    }
    return
  }

  /*
   * Bring the overlay machinery in line with the `open` attribute. Safe to
   * call before the first render (it returns) and repeatedly.
   */
  _syncOpen() {
    if (this._trigger === undefined || this._trigger === null) {
      return
    }
    const isOpen = this.hasAttribute("open")
    this._trigger.setAttribute("aria-expanded", isOpen === true ? "true" : "false")

    if (isOpen === true) {
      if (this._disposePosition === null) {
        this._disposePosition = autoPosition(this._popup, this._trigger, { placement: "bottom-start" })
        this._disposeTrap = trapFocus(this._popup, this._searchInput)
      }
    } else {
      /*
       * Focus returns to the trigger only when it was still inside the popup
       * (Escape, a pick). After an outside click focus is already where the
       * user put it and must stay there.
       */
      const wasOpen = this._disposePosition !== null
      const focusInside = this._popup.contains(this.shadowRoot.activeElement)
      this._releaseOverlay()
      if (wasOpen === true && focusInside === true) {
        this._trigger.focus()
      }
    }
    return
  }

  _open() {
    if (this._isDisabled() === true) {
      return
    }
    const proceed = this.emit("mj-open", {}, { cancelable: true })
    if (proceed === false) {
      return
    }
    this.setAttribute("open", "")
    return
  }

  _close() {
    if (this.hasAttribute("open") === false) {
      return
    }
    this.removeAttribute("open")
    this.emit("mj-close", {})
    return
  }

  _onTriggerClick() {
    if (this.hasAttribute("open")) {
      this._close()
    } else {
      this._open()
    }
    return
  }

  /* Escape closes the dialog from anywhere inside it and returns to the trigger. */
  _onPopupKeydown(event) {
    if (event.key === "Escape") {
      event.preventDefault()
      event.stopPropagation()
      this._close()
      this._trigger.focus()
    }
    return
  }

  _onDocClick(event) {
    if (this.hasAttribute("open") === false) {
      return
    }
    const inside = event.composedPath().includes(this)
    if (inside === false) {
      this._close()
    }
    return
  }

  /* ----- scriptable API ----- */

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    if (value === true) {
      this._open()
    } else {
      this._close()
    }
    return
  }

  /* The selected asset id (comma-separated ids in multiple mode). */
  get value() {
    return this._value
  }

  set value(val) {
    const text = val !== null && val !== undefined ? String(val) : ""
    this._applyValue(text)
    return
  }

  /* The full asset list. Assigning replaces it (and the built-in emoji). */
  get assets() {
    return this._assets.slice()
  }

  set assets(list) {
    this._dataSource = null
    this._loadSeq = this._loadSeq + 1
    this._setAssets(list)
    return
  }

  get dataSource() {
    return this._dataSource
  }

  set dataSource(source) {
    this._dataSource = source !== undefined ? source : null
    if (this._dataSource === null) {
      this._loadSeq = this._loadSeq + 1
      this._assetsSupplied = false
      this._loadBuiltinAssets()
      if (this._assetGrid !== undefined && this._assetGrid !== null) {
        this._activeCategory = null
        this._applyFilter()
        this._renderCategories()
        this._updateTrigger()
      }
    } else {
      this._assetsSupplied = true
      this._loadFromDataSource()
    }
    return
  }

  get selectedAssets() {
    const selected = []
    this._selectedIds.forEach((id) => {
      const asset = this._findAsset(id)
      if (asset !== null) {
        selected.push(asset)
      }
    })
    return selected
  }

  get recentAssets() {
    return this._recentAssets.slice()
  }

  focus(options) {
    if (this._trigger !== undefined && this._trigger !== null) {
      this._trigger.focus(options)
    }
    return
  }
}
