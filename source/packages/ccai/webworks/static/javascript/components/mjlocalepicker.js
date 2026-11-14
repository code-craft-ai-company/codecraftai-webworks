/*
 * mjlocalepicker.js
 *
 * <mj-locale-picker> — specialized combobox over language, country/region,
 * or full locale datasets using Intl APIs for display names.
 *
 * Built-in datasets (names come from Intl.DisplayNames, so they follow the
 * `display-locale`):
 *   mode="language"  the ISO 639-1 language codes         value e.g. "fr"
 *   mode="country"   the ISO 3166-1 alpha-2 region codes  value e.g. "FR"
 *   mode="locale"    common language-region locales       value e.g. "fr-FR"
 * `allowed` / `excluded` (JSON arrays of codes) narrow the list. The
 * `dataSource` property replaces it: an array of
 * `{ code, nativeName, displayName, flag? }`, or an object with
 * `query(request)` (the core DataSource contract) resolving to such items.
 *
 * The `value` attribute is the INITIAL selection; choosing an option updates
 * the `value` property and the form value but is not written back to the
 * attribute, so a form reset can restore what the author wrote.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { autoPosition } from "../core/overlay.js";
import { announce } from "../core/announcer.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: inline-block; vertical-align: middle; }
:host([block]) { display: block; }

.field {
  display: flex;
  align-items: center;
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-locale-picker-border-radius, var(--mj-radius-md));
  background: var(--mj-surface);
  min-height: var(--mj-control-height-md);
  transition: border-color var(--mj-motion-fast);
  overflow: hidden;
}
.field:focus-within { border-color: var(--mj-accent); }
:host([invalid]) .field { border-color: var(--mj-color-danger); }
:host([disabled]) .field,
:host(:disabled) .field { opacity: 0.55; pointer-events: none; }

.flag {
  padding: 0 var(--mj-space-2);
  font-size: var(--mj-locale-picker-flag-size, 1.25rem);
  flex-shrink: 0;
  line-height: 1;
}

.input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  padding: 0 var(--mj-space-2);
  font: inherit;
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
  min-height: var(--mj-control-height-md);
}

.input:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: -2px;
  border-radius: var(--mj-radius-sm);
}

.clear-btn, .toggle-btn {
  flex-shrink: 0;
  padding: 0 var(--mj-space-2);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-text-muted);
  display: flex;
  align-items: center;
  align-self: stretch;
}
.toggle-btn:hover { color: var(--mj-text); }
.toggle-btn:disabled, .clear-btn:disabled { cursor: not-allowed; }
:host([open]) .toggle-btn svg { transform: rotate(180deg); }
.clear-btn.hidden { display: none; }
:host(:not([clearable])) .clear-btn { display: none; }
.clear-btn:hover { color: var(--mj-text); }
.clear-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.popup {
  position: fixed;
  background: var(--mj-surface-raised, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-locale-picker-border-radius, var(--mj-radius-md));
  box-shadow: var(--mj-elevation-2);
  max-height: var(--mj-locale-picker-popup-max-height, 18rem);
  overflow-y: auto;
  z-index: var(--mj-layer-popover);
  display: none;
}
:host([open]) .popup { display: block; }

.listbox { padding: var(--mj-space-1) 0; }

.option {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-space-2) var(--mj-space-3);
  min-height: var(--mj-locale-picker-option-height, 2.5rem);
  cursor: pointer;
  color: var(--mj-text);
}
.option:hover, .option.focused { background: var(--mj-bg-muted); }
.option[aria-selected="true"] { background: var(--mj-bg-subtle); }

.option-flag { font-size: var(--mj-locale-picker-flag-size, 1.25rem); flex-shrink: 0; }
.option-names { display: flex; flex-direction: column; flex: 1; min-width: 0; }
.option-native { font-size: var(--mj-font-size-sm); font-weight: var(--mj-font-weight-medium); }
.option-english { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); }
.option-code {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-locale-picker-code-color, var(--mj-text-muted));
  font-family: var(--mj-font-mono);
  flex-shrink: 0;
}
.check {
  width: 1em; height: 1em; color: var(--mj-accent); flex-shrink: 0;
  opacity: 0;
}
.option[aria-selected="true"] .check { opacity: 1; }

.no-results {
  padding: var(--mj-space-3);
  text-align: center;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
}
`;

/* ISO 3166-1 alpha-2 region codes. */
const COUNTRY_CODES = (
  "AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ " +
  "CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR " +
  "GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP " +
  "KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT " +
  "MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW " +
  "SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ " +
  "UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW"
).split(" ");

/* ISO 639-1 language codes. */
const LANGUAGE_CODES = (
  "aa ab ae af ak am an ar as av ay az ba be bg bi bm bn bo br bs ca ce ch co cr cs cu cv cy da de dv dz ee el en eo es " +
  "et eu fa ff fi fj fo fr fy ga gd gl gn gu gv ha he hi ho hr ht hu hy hz ia id ie ig ii ik io is it iu ja jv ka kg ki " +
  "kj kk kl km kn ko kr ks ku kv kw ky la lb lg li ln lo lt lu lv mg mh mi mk ml mn mr ms mt my na nb nd ne ng nl nn no " +
  "nr nv ny oc oj om or os pa pi pl ps pt qu rm rn ro ru rw sa sc sd se sg si sk sl sm sn so sq sr ss st su sv sw ta te " +
  "tg th ti tk tl tn to tr ts tt tw ty ug uk ur uz ve vi vo wa wo xh yi yo za zh zu"
).split(" ");

/* Common language-region locales (BCP 47). */
const LOCALE_CODES = (
  "af-ZA am-ET ar-AE ar-BH ar-DZ ar-EG ar-IQ ar-JO ar-KW ar-LB ar-LY ar-MA ar-OM ar-QA ar-SA ar-SY ar-TN ar-YE az-AZ " +
  "be-BY bg-BG bn-BD bn-IN bs-BA ca-ES cs-CZ cy-GB da-DK de-AT de-CH de-DE de-LI de-LU el-CY el-GR en-AU en-BZ en-CA " +
  "en-GB en-HK en-IE en-IN en-JM en-MY en-NZ en-PH en-SG en-TT en-US en-ZA en-ZW es-AR es-BO es-CL es-CO es-CR es-DO " +
  "es-EC es-ES es-GT es-HN es-MX es-NI es-PA es-PE es-PR es-PY es-SV es-US es-UY es-VE et-EE eu-ES fa-IR fi-FI fil-PH " +
  "fo-FO fr-BE fr-CA fr-CH fr-FR fr-LU fr-MC ga-IE gl-ES gu-IN he-IL hi-IN hr-BA hr-HR hu-HU hy-AM id-ID is-IS it-CH " +
  "it-IT ja-JP ka-GE kk-KZ km-KH kn-IN ko-KR ky-KG lo-LA lt-LT lv-LV mk-MK ml-IN mn-MN mr-IN ms-BN ms-MY mt-MT my-MM " +
  "nb-NO ne-NP nl-BE nl-NL nn-NO pa-IN pl-PL ps-AF pt-BR pt-PT ro-MD ro-RO ru-BY ru-KZ ru-RU ru-UA si-LK sk-SK sl-SI " +
  "sq-AL sr-BA sr-ME sr-RS sv-FI sv-SE sw-KE sw-TZ ta-IN ta-LK te-IN th-TH tr-TR uk-UA ur-IN ur-PK uz-UZ vi-VN zh-CN " +
  "zh-HK zh-SG zh-TW zu-ZA"
).split(" ");

const GLOBE = "\u{1F310}";

/* Built datasets by "mode|display-locale"; the Intl lookups are not free. */
const DATASET_CACHE = new Map();

/* The regional-indicator flag emoji of a two-letter region code. */
function getCountryFlag(code) {
  let flag = GLOBE
  if (/^[A-Za-z]{2}$/.test(code) === true) {
    const upper = code.toUpperCase()
    const codePoints = Array.from(upper).map((ch) => 0x1F1E6 + ch.charCodeAt(0) - 65)
    flag = String.fromCodePoint(...codePoints)
  }
  return flag
}

function createDisplayNames(locale, type) {
  let names = null
  try {
    names = new Intl.DisplayNames([locale], { type: type, fallback: "none" })
  } catch (error) {
    names = null
  }
  return names
}

function lookupName(names, code) {
  let name = null
  if (names !== null) {
    try {
      const found = names.of(code)
      if (found !== undefined && found !== null && found !== "") {
        name = found
      }
    } catch (error) {
      name = null
    }
  }
  return name
}

/*
 * Describe one code as `{ code, nativeName, displayName, flag }`, or null
 * when Intl does not know it. `displayNames` is the Intl.DisplayNames of the
 * display locale for the mode's type.
 */
function describeCode(mode, code, displayNames) {
  const displayName = lookupName(displayNames, code)
  if (displayName === null) {
    return null
  }

  let nativeName = displayName
  let flag = ""
  if (mode === "country") {
    flag = getCountryFlag(code)
  } else {
    /* The name of a language or locale in that language itself. */
    const own = lookupName(createDisplayNames(code, "language"), code)
    if (own !== null) {
      nativeName = own
    }
    if (mode === "locale") {
      const region = code.split("-").pop()
      flag = getCountryFlag(region)
    }
  }

  const item = { code: code, nativeName: nativeName, displayName: displayName, flag: flag }
  return item
}

function codesForMode(mode) {
  let codes = LANGUAGE_CODES
  if (mode === "country") {
    codes = COUNTRY_CODES
  } else if (mode === "locale") {
    codes = LOCALE_CODES
  }
  return codes
}

function buildDataset(mode, displayLocale) {
  const key = `${mode}|${displayLocale}`
  let items = DATASET_CACHE.get(key)

  if (items === undefined) {
    const displayNames = createDisplayNames(displayLocale, mode === "country" ? "region" : "language")
    const codes = codesForMode(mode)
    items = []
    for (let index = 0; index < codes.length; index = index + 1) {
      const item = describeCode(mode, codes[index], displayNames)
      if (item !== null) {
        items.push(item)
      }
    }
    items.sort((left, right) => left.displayName.localeCompare(right.displayName, displayLocale))
    DATASET_CACHE.set(key, items)
  }

  return items
}

/* Lower-case and strip diacritics so "francais" finds "français". */
function foldText(text) {
  const folded = String(text || "").normalize("NFKD").replace(/\p{M}/gu, "").toLowerCase()
  return folded
}

export class MjLocalePicker extends FormControlMixin(MjElement) {
  static tagName = "mj-locale-picker";
  static styles = STYLES;
  static watched = [
    "value", "mode", "open", "disabled", "readonly", "required", "invalid", "clearable", "allowed", "excluded",
    "show-flag", "show-code", "show-native-name", "display-locale", "placeholder", "aria-label"
  ];

  constructor() {
    super()
    this._initFormControl()
    this._inputValue = ""

    /* The options after allowed / excluded; null until first needed. */
    this._allOptions = null
    this._filteredOptions = []

    /* Items supplied through `dataSource` (null = built-in dataset). */
    this._customOptions = null
    this._dataSource = null
    this._loadSeq = 0

    this._focusedIndex = -1
    this._selectedLocale = null
    this._disposePosition = null
    this._listboxId = nextId("mj-lp-lb")
    this._inputId = nextId("mj-lp-in")

    /* True when the `value` attribute was applied before the first render. */
    this._valueReplayPending = false

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    this._input = null
  }

  render() {
    const markup = html`
      <div class="field" part="field">
        <span class="flag" part="trigger-icon" aria-hidden="true"><slot name="trigger-icon"><span class="flag-glyph">${GLOBE}</span></slot></span>
        <input
          class="input"
          part="input"
          id="${this._inputId}"
          role="combobox"
          aria-haspopup="listbox"
          aria-expanded="false"
          aria-autocomplete="list"
          aria-controls="${this._listboxId}"
          autocomplete="off"
          type="text"
        />
        <button class="clear-btn hidden" part="clear" type="button" aria-label="${t("mj.localePicker.clearSelection")}">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M12 4 8 8l4 4-1 1-4-4-4 4-1-1 4-4-4-4 1-1 4 4 4-4z"/>
          </svg>
        </button>
        <button class="toggle-btn" part="toggle" type="button" tabindex="-1" aria-label="${t("mj.localePicker.showOptions")}">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M3 6l5 5 5-5"/>
          </svg>
        </button>
      </div>
      <div class="popup" part="popup">
        <div class="listbox" part="listbox" id="${this._listboxId}" role="listbox"></div>
        <div class="no-results" part="no-results" hidden><slot name="no-results">${t("core.noResults")}</slot></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._field = this.$(".field")
    this._input = this.$(".input")
    this._popup = this.$(".popup")
    this._listbox = this.$(".listbox")
    this._noResults = this.$(".no-results")
    this._clearBtn = this.$(".clear-btn")
    this._toggleBtn = this.$(".toggle-btn")
    this._flagGlyph = this.$(".flag-glyph")

    this.listen(this._input, "input", this._onInput.bind(this))
    this.listen(this._input, "keydown", this._onKeydown.bind(this))
    this.listen(this._input, "click", this._onInputClick.bind(this))
    this.listen(this._toggleBtn, "click", this._onToggleClick.bind(this))
    this.listen(this._clearBtn, "click", this._onClear.bind(this))
    this.listen(this.shadowRoot, "focusout", this._onFocusOut.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))

    /* One listener each; the options are rebuilt on every keystroke. */
    this.listen(this._listbox, "mousedown", (event) => {
      /* Keep focus in the input while an option is clicked. */
      event.preventDefault()
    })
    this.listen(this._listbox, "click", this._onOptionClick.bind(this))
    this.listen(this._listbox, "mouseover", this._onOptionHover.bind(this))

    /* Everything below paints the fresh shadow DOM from the fields. */
    this._syncLabels()
    this._syncEditable()
    this._refreshSelection()
    this._syncOpen()
    return
  }

  onDisconnected() {
    /* A removed picker must not keep tracking scroll and resize. */
    if (this._disposePosition !== null) {
      this._disposePosition()
      this._disposePosition = null
    }
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
    if (name === "mode" || name === "allowed" || name === "excluded" || name === "display-locale") {
      /* The dataset changed: rebuild it and show the value under the new one. */
      this._allOptions = null
      this._syncLabels()
      this._refreshSelection()
      this._rerenderIfOpen()
    }
    if (name === "show-flag" || name === "show-code" || name === "show-native-name") {
      this._refreshSelection()
      this._rerenderIfOpen()
    }
    if (name === "placeholder" || name === "aria-label") {
      this._syncLabels()
    }
    if (name === "disabled" || name === "readonly" || name === "clearable") {
      this._syncEditable()
      this._syncClearBtn()
    }
    if (name === "required" && this._internals !== undefined) {
      this._refreshValidity()
    }
    if (name === "open") {
      this._syncOpen()
    }
    return
  }

  /* An ancestor <fieldset disabled> was switched on or off. */
  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    this._syncEditable()
    this._syncClearBtn()
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

  /* ----- dataset ----- */

  _mode() {
    const raw = this.getAttribute("mode") || "language"
    const mode = raw === "country" || raw === "locale" ? raw : "language"
    return mode
  }

  _displayLocale() {
    const locale = this.getAttribute("display-locale") || navigator.language || "en"
    return locale
  }

  /* A JSON array attribute as a list of lower-cased codes ([] when absent or malformed). */
  _codeList(name) {
    const raw = this.getAttribute(name) || ""
    let codes = []
    if (raw.length > 0) {
      try {
        const parsed = JSON.parse(raw)
        if (Array.isArray(parsed) === true) {
          codes = parsed.map((code) => String(code).toLowerCase())
        }
      } catch (error) {
        codes = []
      }
    }
    return codes
  }

  /* The options offered: the dataset (or `dataSource` items) after allowed / excluded. */
  _options() {
    if (this._allOptions === null) {
      let items = this._customOptions !== null ? this._customOptions : buildDataset(this._mode(), this._displayLocale())

      const allowed = this._codeList("allowed")
      if (allowed.length > 0) {
        items = items.filter((item) => allowed.indexOf(item.code.toLowerCase()) >= 0)
      }
      const excluded = this._codeList("excluded")
      if (excluded.length > 0) {
        items = items.filter((item) => excluded.indexOf(item.code.toLowerCase()) < 0)
      }

      this._allOptions = items
    }
    return this._allOptions
  }

  /*
   * The item for a code, or null when it is unknown. A single code is
   * described directly, so showing an initial value does not build the
   * whole dataset.
   */
  _findOption(code) {
    const wanted = String(code).toLowerCase()
    let found = null

    if (this._customOptions !== null || this._allOptions !== null) {
      const match = this._options().find((opt) => opt.code.toLowerCase() === wanted)
      found = match !== undefined ? match : null
    }

    if (found === null && this._customOptions === null) {
      const mode = this._mode()
      const canonical = codesForMode(mode).find((candidate) => candidate.toLowerCase() === wanted)
      if (canonical !== undefined) {
        const displayNames = createDisplayNames(this._displayLocale(), mode === "country" ? "region" : "language")
        found = describeCode(mode, canonical, displayNames)
      }
    }

    return found
  }

  /* Turn `dataSource` items into LocaleItems. */
  _normalizeItems(list) {
    const items = []
    const entries = Array.isArray(list) === true ? list : []
    for (let index = 0; index < entries.length; index = index + 1) {
      const entry = entries[index]
      if (entry !== null && typeof entry === "object" && entry.code !== null && entry.code !== undefined) {
        const code = String(entry.code)
        const displayName = entry.displayName !== null && entry.displayName !== undefined ? String(entry.displayName) : code
        const nativeName = entry.nativeName !== null && entry.nativeName !== undefined ? String(entry.nativeName) : displayName
        const flag = entry.flag !== null && entry.flag !== undefined ? String(entry.flag) : ""
        items.push({ code: code, nativeName: nativeName, displayName: displayName, flag: flag })
      }
    }
    return items
  }

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
      } else if (typeof source === "function") {
        result = await source({ offset: 0, limit: 10000, filter: "" })
      }
    } catch (error) {
      console.error("mj-locale-picker: the data source failed to load", error)
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

    this._customOptions = this._normalizeItems(items)
    this._allOptions = null
    this._refreshSelection()
    this._rerenderIfOpen()
    return
  }

  /* ----- value and field state ----- */

  /* Select `code` (an unknown code is kept and shown as typed). No event is emitted. */
  _applyValue(code) {
    const text = code !== null && code !== undefined ? String(code).trim() : ""
    const found = text.length > 0 ? this._findOption(text) : null

    this._selectedLocale = found
    this._setFormValue(found !== null ? found.code : text)
    this._refreshSelection()
    return
  }

  /* The text the field shows for the current value. */
  _selectionText() {
    let text = this._value || ""
    if (this._selectedLocale !== null) {
      text = this._selectedLocale.displayName
    }
    return text
  }

  /* Re-read the selected item from the dataset and show it in the field. */
  _refreshSelection() {
    const value = this._value || ""
    this._selectedLocale = value.length > 0 ? this._findOption(value) : null
    this._inputValue = this._selectionText()

    if (this._input !== undefined && this._input !== null) {
      this._input.value = this._inputValue
      this._syncFlagIcon()
      this._syncClearBtn()
    }
    return
  }

  _showFlags() {
    const show = this.getAttribute("show-flag") !== "false"
    return show
  }

  /*
   * The flag is written into the slot's fallback content, never into the
   * element that holds the slot, so a slotted trigger icon survives.
   */
  _syncFlagIcon() {
    if (this._flagGlyph === undefined || this._flagGlyph === null) {
      return
    }
    const locale = this._selectedLocale
    let glyph = GLOBE
    if (this._showFlags() === true && locale !== null && locale.flag !== undefined && locale.flag !== "") {
      glyph = locale.flag
    }
    this._flagGlyph.textContent = glyph
    return
  }

  _syncClearBtn() {
    if (this._clearBtn === undefined || this._clearBtn === null) {
      return
    }
    const hasVal = (this._value || "").length > 0
    const clearable = this.hasAttribute("clearable")
    if (clearable === true && hasVal === true && this._isEditable() === true) {
      this._clearBtn.classList.remove("hidden")
    } else {
      this._clearBtn.classList.add("hidden")
    }
    return
  }

  /* Disabled by its own attribute or by an ancestor <fieldset disabled>. */
  _isDisabled() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    return disabled
  }

  _isEditable() {
    const blocked = this._isDisabled() === true || this.hasAttribute("readonly") === true
    return blocked === false
  }

  /* Mirror disabled / readonly onto the inner controls. */
  _syncEditable() {
    if (this._input === undefined || this._input === null) {
      return
    }
    const editable = this._isEditable()
    this._input.disabled = this._isDisabled()
    this._input.readOnly = this.hasAttribute("readonly")
    this._clearBtn.disabled = editable === false
    this._toggleBtn.disabled = editable === false
    if (editable === false && this.hasAttribute("open") === true) {
      this._revert()
      this._close()
    }
    return
  }

  /* The placeholder and accessible names, which follow the mode. */
  _syncLabels() {
    if (this._input === undefined || this._input === null) {
      return
    }
    const mode = this._mode()
    let fallback = t("mj.localePicker.selectLanguage")
    let listLabel = t("mj.localePicker.languages")
    if (mode === "country") {
      fallback = t("mj.localePicker.selectCountry")
      listLabel = t("mj.localePicker.countries")
    } else if (mode === "locale") {
      fallback = t("mj.localePicker.selectLocale")
      listLabel = t("mj.localePicker.locales")
    }

    const placeholder = this.getAttribute("placeholder") || fallback
    this._input.placeholder = placeholder
    this._input.setAttribute("aria-label", this.getAttribute("aria-label") || placeholder)
    this._listbox.setAttribute("aria-label", listLabel)
    return
  }

  /* ----- options ----- */

  _filterOptions(query) {
    const all = this._options()
    if (query.length === 0) {
      return all.slice()
    }
    const q = foldText(query)
    return all.filter((opt) => {
      const native = foldText(opt.nativeName)
      const display = foldText(opt.displayName)
      const code = foldText(opt.code)
      return native.includes(q) || display.includes(q) || code.includes(q)
    })
  }

  /*
   * The text to filter by. While the field still shows the committed
   * selection the user has not asked for anything narrower, so the whole
   * list is offered.
   */
  _currentQuery() {
    const text = this._input.value
    const query = text === this._selectionText() ? "" : text
    return query
  }

  _rerenderIfOpen() {
    if (this._input !== undefined && this._input !== null && this.hasAttribute("open") === true) {
      this._renderOptions(this._currentQuery())
    }
    return
  }

  _renderOptions(query) {
    const filtered = this._filterOptions(query || "")
    this._filteredOptions = filtered
    const showNative = this.getAttribute("show-native-name") !== "false"
    const showCode = this.hasAttribute("show-code") === true && this.getAttribute("show-code") !== "false"
    const showFlag = this._showFlags()
    const selectedCode = (this._value || "").toLowerCase()

    this._focusedIndex = -1
    this._input.removeAttribute("aria-activedescendant")
    this._noResults.hidden = filtered.length > 0
    this._listbox.hidden = filtered.length === 0

    if (filtered.length === 0) {
      this._listbox.textContent = ""
      announce(t("mj.localePicker.noResultsFound"), "polite")
      return
    }

    const rows = filtered.map((opt, idx) => {
      const isSelected = selectedCode.length > 0 && opt.code.toLowerCase() === selectedCode
      const sameName = opt.nativeName === opt.displayName
      const flagHtml = showFlag === true && opt.flag !== undefined && opt.flag.length > 0
        ? html`<span class="option-flag" part="option-flag" aria-hidden="true">${opt.flag}</span>`
        : ""
      const nativeHtml = showNative === true && sameName === false
        ? html`<span class="option-native" part="option-native-name" dir="auto">${opt.nativeName}</span>`
        : ""
      const englishHtml = html`<span class="${nativeHtml === "" ? "option-native" : "option-english"}" part="option-english-name">${opt.displayName}</span>`
      const codeHtml = showCode === true
        ? html`<span class="option-code" part="option-code">${opt.code}</span>`
        : ""
      const ariaLabel = sameName === true ? opt.displayName : `${opt.nativeName} – ${opt.displayName}`

      return html`<div
        class="option"
        part="option"
        role="option"
        id="${this._listboxId}-opt-${idx}"
        aria-selected="${isSelected === true ? "true" : "false"}"
        data-idx="${idx}"
        aria-label="${ariaLabel}"
      >
        ${flagHtml}
        <span class="option-names">
          ${nativeHtml}
          ${englishHtml}
        </span>
        ${codeHtml}
        <svg class="check" aria-hidden="true" viewBox="0 0 16 16" fill="currentColor">
          <path d="M13.5 3.5 6 11 2.5 7.5l1-1L6 9 12.5 2.5z"/>
        </svg>
      </div>`
    })
    this._listbox.innerHTML = String(html`${rows}`)

    /* Bring the current selection into view when the whole list is shown. */
    const selectedNode = this._listbox.querySelector(".option[aria-selected='true']")
    if (selectedNode !== null && typeof selectedNode.scrollIntoView === "function") {
      selectedNode.scrollIntoView({ block: "nearest" })
    }
    return
  }

  _optionNodes() {
    const nodes = Array.from(this._listbox.querySelectorAll(".option"))
    return nodes
  }

  _setFocused(index) {
    const opts = this._optionNodes()
    opts.forEach((o) => o.classList.remove("focused"))
    const opt = opts[index]
    if (opt !== undefined) {
      opt.classList.add("focused")
      opt.scrollIntoView({ block: "nearest" })
      this._focusedIndex = index
      this._input.setAttribute("aria-activedescendant", opt.id)
    }
    return
  }

  _onOptionHover(event) {
    const node = event.target.closest(".option")
    if (node === null) {
      return
    }
    const index = parseInt(node.dataset.idx, 10)
    if (index !== this._focusedIndex) {
      const opts = this._optionNodes()
      opts.forEach((o) => o.classList.remove("focused"))
      node.classList.add("focused")
      this._focusedIndex = index
      this._input.setAttribute("aria-activedescendant", node.id)
    }
    return
  }

  _onOptionClick(event) {
    const node = event.target.closest(".option")
    if (node !== null) {
      this._commitIndex(parseInt(node.dataset.idx, 10))
    }
    return
  }

  /* The user chose the option at `index` of the shown list. */
  _commitIndex(index) {
    const locale = this._filteredOptions[index]
    if (locale === undefined || this._isEditable() === false) {
      return
    }
    const prevValue = this._value
    this._selectedLocale = locale
    this._setFormValue(locale.code)
    this._refreshSelection()
    this._close()
    this._input.focus()
    if (prevValue !== locale.code) {
      this.emit("mj-change", { value: locale.code, previousValue: prevValue, locale: locale })
    }
    return
  }

  /* ----- open / close ----- */

  _open() {
    if (this._isEditable() === false || this.hasAttribute("open") === true) {
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

  /*
   * Bring the popup in line with the `open` attribute. Safe to call before
   * the first render (it returns) and repeatedly.
   */
  _syncOpen() {
    if (this._input === undefined || this._input === null) {
      return
    }
    const isOpen = this.hasAttribute("open")
    this._input.setAttribute("aria-expanded", isOpen === true ? "true" : "false")
    this._toggleBtn.setAttribute("aria-label", isOpen === true ? t("mj.localePicker.hideOptions") : t("mj.localePicker.showOptions"))

    if (isOpen === true) {
      this._renderOptions(this._currentQuery())
      if (this._disposePosition === null) {
        this._popup.style.minWidth = `${this._field.offsetWidth}px`
        this._disposePosition = autoPosition(this._popup, this._field, { placement: "bottom-start" })
      }
    } else {
      this._input.removeAttribute("aria-activedescendant")
      this._focusedIndex = -1
      if (this._disposePosition !== null) {
        this._disposePosition()
        this._disposePosition = null
      }
    }
    return
  }

  /* ----- field events ----- */

  _onInput() {
    if (this._isEditable() === false) {
      return
    }
    this._inputValue = this._input.value
    this.emit("mj-input", { inputValue: this._inputValue })
    if (this.hasAttribute("open") === true) {
      this._renderOptions(this._currentQuery())
    } else {
      this._open()
    }
    return
  }

  /* A pointer user opens the list by clicking the field. */
  _onInputClick() {
    this._open()
    return
  }

  _onToggleClick() {
    if (this.hasAttribute("open") === true) {
      this._revert()
      this._close()
    } else {
      this._open()
    }
    this._input.focus()
    return
  }

  _onKeydown(event) {
    const isOpen = this.hasAttribute("open")
    const count = isOpen === true ? this._optionNodes().length : 0

    /* The Alt combinations are tested first: the plain arrows would match them too. */
    if (event.altKey === true && event.key === "ArrowDown") {
      event.preventDefault()
      this._open()
    } else if (event.altKey === true && event.key === "ArrowUp") {
      event.preventDefault()
      if (isOpen === true) {
        this._revert()
        this._close()
      }
    } else if (event.key === "ArrowDown") {
      event.preventDefault()
      if (isOpen === false) {
        this._open()
      } else {
        this._setFocused(Math.min(this._focusedIndex + 1, count - 1))
      }
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      if (isOpen === false) {
        this._open()
      } else {
        this._setFocused(Math.max(this._focusedIndex - 1, 0))
      }
    } else if (event.key === "Home" && isOpen === true) {
      event.preventDefault()
      this._setFocused(0)
    } else if (event.key === "End" && isOpen === true) {
      event.preventDefault()
      this._setFocused(count - 1)
    } else if (event.key === "Enter" && isOpen === true) {
      event.preventDefault()
      if (this._focusedIndex >= 0) {
        this._commitIndex(this._focusedIndex)
      } else if (this._filteredOptions.length === 1) {
        /* Typing down to a single match and pressing Enter picks it. */
        this._commitIndex(0)
      }
    } else if (event.key === "Escape") {
      if (isOpen === true) {
        event.preventDefault()
        this._revert()
        this._close()
      }
    } else if (event.key === "Tab") {
      if (isOpen === true) {
        this._revert()
        this._close()
      }
    }
    return
  }

  /* Put the committed selection's text back into the field. */
  _revert() {
    this._inputValue = this._selectionText()
    this._input.value = this._inputValue
    return
  }

  /* Focus left the component: drop what was typed and close. */
  _onFocusOut(event) {
    const next = event.relatedTarget
    if (next !== null && next !== undefined && this.shadowRoot.contains(next) === true) {
      return
    }
    this._revert()
    this._close()
    return
  }

  _onClear() {
    if (this._isEditable() === false) {
      return
    }
    const prevValue = this._value
    this._applyValue("")
    this._close()
    this.emit("mj-change", { value: "", previousValue: prevValue, locale: null })
    this.emit("mj-clear", {})
    this._input.focus()
    return
  }

  _onDocClick(event) {
    if (this.hasAttribute("open") === false) {
      return
    }
    const inside = event.composedPath().includes(this)
    if (inside === false) {
      this._revert()
      this._close()
    }
    return
  }

  _validationAnchor() {
    const anchor = this._input !== undefined ? this._input : null
    return anchor
  }

  /* ----- scriptable API ----- */

  /* The selected code. */
  get value() {
    return this._value
  }

  set value(next) {
    this._applyValue(next)
    return
  }

  get selectedLocale() {
    return this._selectedLocale
  }

  get inputValue() {
    return this._inputValue
  }

  /* A custom dataset: an array of LocaleItems or an object with `query(request)`. */
  get dataSource() {
    return this._dataSource
  }

  set dataSource(source) {
    this._dataSource = source !== undefined ? source : null
    if (this._dataSource === null) {
      this._loadSeq = this._loadSeq + 1
      this._customOptions = null
      this._allOptions = null
      this._refreshSelection()
      this._rerenderIfOpen()
    } else {
      this._loadFromDataSource()
    }
    return
  }

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

  focus(options) {
    if (this._input !== undefined && this._input !== null) {
      this._input.focus(options)
    }
    return
  }
}
