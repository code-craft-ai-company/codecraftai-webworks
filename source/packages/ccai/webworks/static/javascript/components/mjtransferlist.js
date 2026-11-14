import { MjElement, nextId } from '../core/mjelement.js';
import { FormControlMixin } from '../core/forminternals.js';
import { announce } from '../core/announcer.js';
import { html } from '../core/html.js';
import { t } from '../core/intl.js';

/*
 * mj-transfer-list -- two listboxes with buttons that move items between an
 * "available" (source) pool and a "selected" (target) pool.
 *
 * State lives in fields and the shadow DOM is rebuilt from them:
 *   _sourceItems / _targetItems        the two pools, in display order
 *   _sourceSelected / _targetSelected  values highlighted in each listbox
 *   _active                            the keyboard-active value per listbox
 *
 * Items come from light-DOM <mj-option> children (an option with `selected`
 * starts in the target) or from the `items` property. Option children are
 * observed: options added later appear, removed ones disappear, and items
 * the user already moved stay where they are.
 *
 * Each listbox keeps DOM focus itself and points at its active option with
 * aria-activedescendant, so re-rendering the options never drops focus. The
 * option rows are only rebuilt when the shown items change; selection and
 * the active option are updated on the existing rows. A pointer press that
 * focuses a listbox therefore still lands its click on the row it pressed.
 *
 * The `value` attribute is the INITIAL target content (comma-separated
 * values); user moves are not reflected back to it. Read the current state
 * from the `value` property or `targetItems`.
 */
export class MjTransferList extends FormControlMixin(MjElement) {
    static tagName = 'mj-transfer-list';

    static styles = `
        :host {
            display: block;
            font-family: var(--mj-font-sans);
            font-size: var(--mj-font-size-md);
            color: var(--mj-text);
        }
        :host([disabled]) {
            opacity: 0.55;
            pointer-events: none;
        }
        [part="container"] {
            display: flex;
            align-items: stretch;
            gap: var(--mj-transfer-list-gap, var(--mj-space-4));
        }
        :host([orientation="vertical"]) [part="container"] {
            flex-direction: column;
        }
        [part="source-pane"],
        [part="target-pane"] {
            display: flex;
            flex-direction: column;
            flex: 1;
            min-width: var(--mj-transfer-list-pane-min-width, 12rem);
            border: 1px solid var(--mj-border-strong);
            border-radius: var(--mj-transfer-list-border-radius, var(--mj-radius-md));
            background: var(--mj-surface);
            overflow: hidden;
        }
        :host([invalid]) [part="target-pane"] {
            border-color: var(--mj-color-danger);
        }
        [part="source-header"],
        [part="target-header"] {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: var(--mj-space-2);
            padding: var(--mj-space-2) var(--mj-space-3);
            background: var(--mj-bg-subtle);
            border-block-end: 1px solid var(--mj-border);
            font-weight: var(--mj-font-weight-bold);
            font-size: var(--mj-font-size-sm);
        }
        .pane-count {
            color: var(--mj-text-muted);
            font-weight: var(--mj-font-weight-regular);
            white-space: nowrap;
        }
        [part="source-search"],
        [part="target-search"] {
            padding: var(--mj-space-2) var(--mj-space-3);
            border-block-end: 1px solid var(--mj-border);
        }
        [part="source-search"] input,
        [part="target-search"] input {
            width: 100%;
            padding: var(--mj-space-1) var(--mj-space-2);
            border: 1px solid var(--mj-border-strong);
            border-radius: var(--mj-radius-sm);
            background: var(--mj-surface);
            font-family: inherit;
            font-size: var(--mj-font-size-sm);
            color: var(--mj-text);
            outline: none;
        }
        [part="source-search"] input:focus,
        [part="target-search"] input:focus {
            border-color: var(--mj-accent);
            outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
            outline-offset: 1px;
        }
        [part="source-listbox"],
        [part="target-listbox"] {
            flex: 1;
            overflow-y: auto;
            height: var(--mj-transfer-list-pane-height, 16rem);
            padding: var(--mj-space-1);
            outline: none;
        }
        [part="source-listbox"]:focus-visible:not([aria-activedescendant]),
        [part="target-listbox"]:focus-visible:not([aria-activedescendant]) {
            outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
            outline-offset: -2px;
        }
        .list-option {
            display: flex;
            align-items: center;
            gap: var(--mj-space-2);
            padding: var(--mj-space-2) var(--mj-space-3);
            border-inline-start: 3px solid transparent;
            border-radius: var(--mj-radius-sm);
            cursor: pointer;
            user-select: none;
        }
        .list-option:hover {
            background: var(--mj-bg-subtle);
        }
        .list-option[aria-selected="true"] {
            background: var(--mj-bg-muted);
            border-inline-start-color: var(--mj-accent);
            font-weight: var(--mj-font-weight-medium);
        }
        /* The keyboard-active option, shown while its listbox has focus. */
        [role="listbox"]:focus .list-option.active {
            outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
            outline-offset: -2px;
        }
        .list-option[aria-disabled="true"] {
            opacity: 0.45;
            cursor: not-allowed;
        }
        .option-icon {
            width: 1rem;
            height: 1rem;
            flex-shrink: 0;
            color: var(--mj-text-muted);
        }
        [part="empty-source"],
        [part="empty-target"] {
            padding: var(--mj-space-4);
            text-align: center;
            color: var(--mj-text-muted);
            font-size: var(--mj-font-size-sm);
        }
        [part="controls"] {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: var(--mj-transfer-list-controls-gap, var(--mj-space-2));
            width: var(--mj-transfer-list-controls-width, 3rem);
            flex-shrink: 0;
        }
        :host([orientation="vertical"]) [part="controls"] {
            flex-direction: row;
            width: auto;
            height: var(--mj-transfer-list-controls-width, 3rem);
        }
        [part="controls"] button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2rem;
            height: 2rem;
            padding: 0;
            background: var(--mj-surface);
            border: 1px solid var(--mj-border-strong);
            border-radius: var(--mj-radius-sm);
            cursor: pointer;
            font: inherit;
            color: var(--mj-text);
            transition: background var(--mj-motion-fast) var(--mj-motion-ease),
                        border-color var(--mj-motion-fast) var(--mj-motion-ease);
        }
        [part="controls"] button:hover:not(:disabled) {
            background: var(--mj-bg-muted);
            border-color: var(--mj-accent);
        }
        [part="controls"] button:focus-visible {
            outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
            outline-offset: var(--mj-focus-ring-offset);
        }
        [part="controls"] button:disabled {
            opacity: 0.45;
            cursor: not-allowed;
        }
        /*
         * The move glyphs point from the source pane to the target pane:
         * mirrored in right-to-left layouts, turned downwards when stacked.
         */
        .glyph {
            display: inline-block;
            line-height: 1;
        }
        :host(:dir(rtl)) .glyph.directional {
            transform: scaleX(-1);
        }
        :host([orientation="vertical"]) .glyph.directional {
            transform: rotate(90deg);
        }
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0,0,0,0);
            white-space: nowrap;
            border: 0;
        }
    `;

    static watched = ['name', 'value', 'disabled', 'required', 'reorder', 'searchable',
        'orientation', 'source-label', 'target-label', 'max-target'];

    constructor() {
        super();
        this._initFormControl();

        this._sourceItems = [];
        this._targetItems = [];
        this._sourceSelected = new Set();
        this._targetSelected = new Set();
        this._sourceFilter = '';
        this._targetFilter = '';
        this._liveId = nextId('mj-tl-live');
        this._srcHeaderId = nextId('mj-tl-src-hdr');
        this._tgtHeaderId = nextId('mj-tl-tgt-hdr');
        this._optionIdPrefix = nextId('mj-tl-opt');

        /* The keyboard-active value and the Shift-range anchor of each listbox. */
        this._active = { source: null, target: null };
        this._anchor = { source: null, target: null };

        /*
         * Per listbox: the element and the item signature its rows were last
         * built for (see _renderList). A different element (a re-render) or
         * signature rebuilds the rows.
         */
        this._renderedRows = { source: null, target: null };

        /* True once the item pools were filled from the options or `items`. */
        this._itemsInitialised = false;

        /* Items assigned through the `items` property (null when options are used). */
        this._assignedItems = null;

        /*
         * Target values requested through `value` that no item carried yet;
         * an option that arrives later with one of them goes to the target.
         */
        this._wantedTargetValues = [];

        /* True when the `value` attribute was seen before the first render. */
        this._valueReplayPending = false;

        this._formDisabled = false;
        this._optionObserver = null;
    }

    get sourceItems() {
        return this._sourceItems.slice();
    }

    get targetItems() {
        return this._targetItems.slice();
    }

    get allItems() {
        return [...this._sourceItems, ...this._targetItems];
    }

    /* The whole item pool; assigning replaces it (`selected: true` starts in the target). */
    get items() {
        return this.allItems;
    }

    set items(list) {
        const entries = Array.isArray(list) ? list : [];
        this._assignedItems = entries.map((entry) => this._normalizeItem(entry));
        this._itemsInitialised = true;
        this._resetPools();
    }

    /* The target values joined with commas -- the same form as the `value` attribute. */
    get value() {
        return this._targetItems.map((i) => i.value).join(',');
    }

    set value(val) {
        const text = val !== null && val !== undefined ? String(val) : '';
        this._applyValueString(text);
    }

    render() {
        const sourceLabel = this._sourceLabel();
        const targetLabel = this._targetLabel();

        return html`
            <div part="container">
                <div part="source-pane" role="region" aria-labelledby="${this._srcHeaderId}">
                    <div part="source-header" id="${this._srcHeaderId}">
                        <slot name="source-header"><span data-label="source">${sourceLabel}</span></slot>
                        <span class="pane-count" data-count="source">${t('mj.transferList.count', { count: 0 })}</span>
                    </div>
                    <div part="source-search" hidden>
                        <input type="search" data-role="source-filter">
                    </div>
                    <div
                        part="source-listbox"
                        role="listbox"
                        aria-multiselectable="true"
                        tabindex="0"
                        data-list="source"
                    ></div>
                    <div part="empty-source" hidden>
                        <slot name="empty-source">${t('mj.transferList.emptySource')}</slot>
                    </div>
                </div>

                <div part="controls" role="group" aria-label="${t('mj.transferList.controlsLabel')}">
                    <slot name="controls">
                        <button part="move-right" type="button" data-action="move-right" disabled>
                            <span class="glyph directional" aria-hidden="true">›</span>
                        </button>
                        <button part="move-all-right" type="button" data-action="move-all-right" disabled>
                            <span class="glyph directional" aria-hidden="true">»</span>
                        </button>
                        <button part="move-left" type="button" data-action="move-left" disabled>
                            <span class="glyph directional" aria-hidden="true">‹</span>
                        </button>
                        <button part="move-all-left" type="button" data-action="move-all-left" disabled>
                            <span class="glyph directional" aria-hidden="true">«</span>
                        </button>
                        <button part="move-up" type="button" aria-label="${t('mj.transferList.moveUp')}" data-action="move-up" disabled hidden>
                            <span class="glyph" aria-hidden="true">↑</span>
                        </button>
                        <button part="move-down" type="button" aria-label="${t('mj.transferList.moveDown')}" data-action="move-down" disabled hidden>
                            <span class="glyph" aria-hidden="true">↓</span>
                        </button>
                    </slot>
                </div>

                <div part="target-pane" role="region" aria-labelledby="${this._tgtHeaderId}">
                    <div part="target-header" id="${this._tgtHeaderId}">
                        <slot name="target-header"><span data-label="target">${targetLabel}</span></slot>
                        <span class="pane-count" data-count="target">${t('mj.transferList.count', { count: 0 })}</span>
                    </div>
                    <div part="target-search" hidden>
                        <input type="search" data-role="target-filter">
                    </div>
                    <div
                        part="target-listbox"
                        role="listbox"
                        aria-multiselectable="true"
                        tabindex="0"
                        data-list="target"
                    ></div>
                    <div part="empty-target" hidden>
                        <slot name="empty-target">${t('mj.transferList.emptyTarget')}</slot>
                    </div>
                </div>
            </div>
            <div id="${this._liveId}" aria-live="polite" aria-atomic="true" class="sr-only"></div>
        `;
    }

    /*
     * Wire the freshly rendered shadow DOM and paint it from the fields. The
     * item pools are read from the <mj-option> children only on the first
     * connect; afterwards (reconnect) the user's transfers are kept.
     */
    afterRender() {
        const controls = this.$('[part="controls"]');
        this.listen(controls, 'click', (e) => this._onControlClick(e));

        const sides = ['source', 'target'];
        sides.forEach((side) => {
            const lb = this.$(`[part="${side}-listbox"]`);
            this.listen(lb, 'click', (e) => this._onListClick(e, side));
            this.listen(lb, 'keydown', (e) => this._onListKeydown(e, side));
            this.listen(lb, 'focus', () => this._onListFocus(side));

            const filterInput = this.$(`[data-role="${side}-filter"]`);
            filterInput.value = side === 'source' ? this._sourceFilter : this._targetFilter;
            this.listen(filterInput, 'input', (e) => {
                if (side === 'source') {
                    this._sourceFilter = e.currentTarget.value;
                } else {
                    this._targetFilter = e.currentTarget.value;
                }
                this._renderList(side);
            });
        });

        /* Options added, removed or relabelled after the first connect. */
        if (typeof MutationObserver === 'function') {
            const observer = new MutationObserver(() => this._syncFromOptions());
            observer.observe(this, { childList: true, subtree: true, characterData: true, attributes: true,
                attributeFilter: ['value', 'icon', 'disabled'] });
            this._optionObserver = observer;
            this.onTeardown(() => {
                observer.disconnect();
                this._optionObserver = null;
            });
        }

        if (this._itemsInitialised === false) {
            this._itemsInitialised = true;
            this._resetPools();
        } else if (this._assignedItems === null) {
            /* Reconnect: pick up option changes made while detached. */
            this._syncFromOptions();
        }

        this._applyLabels();
        this._applyStructure();
        this._applyDisabledState();
        this._renderLists();
        this._syncFormValue();
    }

    onAttributeChanged(name, oldVal, newVal) {
        if (name === 'value') {
            if (this._rendered === false) {
                /* Applied by afterRender once the item pools exist. */
                this._valueReplayPending = true;
            } else if (this._valueReplayPending === true) {
                this._valueReplayPending = false;
            } else {
                this._applyValueString(newVal || '');
            }
        }
        if (name === 'source-label' || name === 'target-label') {
            this._applyLabels();
        }
        if (name === 'searchable' || name === 'reorder') {
            this._applyStructure();
            this._renderLists();
        }
        if (name === 'disabled') {
            this._applyDisabledState();
            this._updateButtons();
        }
        if (name === 'max-target') {
            this._updateButtons();
        }
        if (name === 'name') {
            this._syncFormValue();
        }
        if (name === 'required') {
            this._refreshValidity();
        }
    }

    onFormDisabled(disabled) {
        this._formDisabled = disabled === true;
        this._applyDisabledState();
        this._updateButtons();
    }

    _validationAnchor() {
        const anchor = this.$('[part="target-listbox"]');
        return anchor;
    }

    _sourceLabel() {
        return this.getAttribute('source-label') || t('mj.transferList.sourceLabel');
    }

    _targetLabel() {
        return this.getAttribute('target-label') || t('mj.transferList.targetLabel');
    }

    _isDisabled() {
        const disabled = this.hasAttribute('disabled') || this._formDisabled === true;
        return disabled;
    }

    /* Turn a string or a loosely shaped object into a TransferItem. */
    _normalizeItem(entry) {
        let item = { value: '', label: '', icon: null, disabled: false, selected: false };

        if (entry !== null && typeof entry === 'object') {
            let value = entry.value;
            let label = entry.label;
            if (value === null || value === undefined) {
                value = label;
            }
            if (label === null || label === undefined) {
                label = value;
            }
            item = {
                value: value !== null && value !== undefined ? String(value) : '',
                label: label !== null && label !== undefined ? String(label) : '',
                icon: entry.icon !== null && entry.icon !== undefined ? String(entry.icon) : null,
                disabled: entry.disabled === true,
                selected: entry.selected === true,
            };
        } else if (entry !== null && entry !== undefined) {
            const text = String(entry);
            item = { value: text, label: text, icon: null, disabled: false, selected: false };
        }

        return item;
    }

    /* The <mj-option> children as items; `selected` marks the initial target side. */
    _readOptions() {
        const items = [];
        this.querySelectorAll('mj-option').forEach((opt) => {
            const label = opt.textContent.trim();
            const value = opt.getAttribute('value') || label;
            const icon = opt.getAttribute('icon') || null;
            const disabled = opt.hasAttribute('disabled');
            const selected = opt.hasAttribute('selected');
            items.push({ value, label, icon, disabled, selected });
        });
        return items;
    }

    _toItem(entry) {
        const item = { value: entry.value, label: entry.label, icon: entry.icon, disabled: entry.disabled };
        return item;
    }

    /*
     * Put every item on its initial side: from the assigned `items` or the
     * <mj-option> children, then the `value` attribute when one is present.
     * Used on first connect, on `items` assignment and on form reset.
     */
    _resetPools() {
        const pool = this._assignedItems !== null ? this._assignedItems : this._readOptions();

        this._sourceItems = pool.filter((entry) => entry.selected !== true).map((entry) => this._toItem(entry));
        this._targetItems = pool.filter((entry) => entry.selected === true).map((entry) => this._toItem(entry));
        this._sourceSelected.clear();
        this._targetSelected.clear();
        this._active = { source: null, target: null };
        this._anchor = { source: null, target: null };
        this._wantedTargetValues = [];

        if (this.hasAttribute('value') === true) {
            this._applyValueString(this.getAttribute('value') || '');
        } else {
            this._renderLists();
            this._syncFormValue();
        }
    }

    /*
     * Reconcile the pools with the current <mj-option> children without
     * undoing the user's transfers: new options are added (to the target when
     * they carry `selected` or a value requested through `value`), removed
     * options are dropped, and labels, icons and disabled flags are refreshed.
     */
    _syncFromOptions() {
        if (this._assignedItems !== null || this._itemsInitialised === false) {
            return;
        }

        const options = this._readOptions();
        const byValue = new Map();
        options.forEach((entry) => byValue.set(entry.value, entry));

        const refresh = (items) => {
            const kept = [];
            items.forEach((item) => {
                const entry = byValue.get(item.value);
                if (entry !== undefined) {
                    kept.push(this._toItem(entry));
                    byValue.delete(item.value);
                }
            });
            return kept;
        };

        const nextSource = refresh(this._sourceItems);
        const nextTarget = refresh(this._targetItems);

        /* Whatever is left in the map is new; keep the option order. */
        options.forEach((entry) => {
            if (byValue.has(entry.value) === true) {
                byValue.delete(entry.value);
                const wanted = this._wantedTargetValues.indexOf(entry.value) >= 0;
                if (entry.selected === true || wanted === true) {
                    nextTarget.push(this._toItem(entry));
                } else {
                    nextSource.push(this._toItem(entry));
                }
            }
        });

        this._sourceItems = nextSource;
        this._targetItems = nextTarget;
        this._pruneSelection();
        this._renderLists();
        this._syncFormValue();
    }

    /* Drop selected and active values whose item left that side. */
    _pruneSelection() {
        const sides = ['source', 'target'];
        sides.forEach((side) => {
            const items = side === 'source' ? this._sourceItems : this._targetItems;
            const selected = side === 'source' ? this._sourceSelected : this._targetSelected;
            const present = new Set(items.map((i) => i.value));

            Array.from(selected).forEach((value) => {
                if (present.has(value) === false) {
                    selected.delete(value);
                }
            });
            if (this._active[side] !== null && present.has(this._active[side]) === false) {
                this._active[side] = null;
            }
            if (this._anchor[side] !== null && present.has(this._anchor[side]) === false) {
                this._anchor[side] = null;
            }
        });
    }

    /*
     * Make the target hold exactly the comma-separated values in `text`, in
     * that order; everything else returns to the source in pool order. An
     * empty string empties the target. No event is emitted.
     */
    _applyValueString(text) {
        const wanted = text.split(',').map((v) => v.trim()).filter((v) => v.length > 0);
        const pool = this._assignedItems !== null ? this._assignedItems : this._readOptions();

        /* Pool order first, then any item the pool no longer lists. */
        const ordered = [];
        const seen = new Set();
        const current = this.allItems;
        pool.forEach((entry) => {
            const item = current.find((i) => i.value === entry.value);
            if (item !== undefined && seen.has(item.value) === false) {
                seen.add(item.value);
                ordered.push(item);
            }
        });
        current.forEach((item) => {
            if (seen.has(item.value) === false) {
                seen.add(item.value);
                ordered.push(item);
            }
        });

        const nextTarget = [];
        wanted.forEach((value) => {
            const item = ordered.find((i) => i.value === value);
            if (item !== undefined && nextTarget.indexOf(item) < 0) {
                nextTarget.push(item);
            }
        });

        this._targetItems = nextTarget;
        this._sourceItems = ordered.filter((item) => nextTarget.indexOf(item) < 0);
        this._wantedTargetValues = wanted;
        this._pruneSelection();
        this._renderLists();
        this._syncFormValue();
    }

    /* Write the pane labels and the texts derived from them. */
    _applyLabels() {
        const sourceLabel = this._sourceLabel();
        const targetLabel = this._targetLabel();

        const setText = (selector, text) => {
            const node = this.$(selector);
            if (node != null) {
                node.textContent = text;
            }
        };
        const setLabel = (selector, text) => {
            const node = this.$(selector);
            if (node != null) {
                node.setAttribute('aria-label', text);
            }
        };

        setText('[data-label="source"]', sourceLabel);
        setText('[data-label="target"]', targetLabel);
        setLabel('[part="source-listbox"]', sourceLabel);
        setLabel('[part="target-listbox"]', targetLabel);
        setLabel('[data-action="move-right"]', t('mj.transferList.moveSelectedTo', { label: targetLabel }));
        setLabel('[data-action="move-all-right"]', t('mj.transferList.moveAllTo', { label: targetLabel }));
        setLabel('[data-action="move-left"]', t('mj.transferList.moveSelectedTo', { label: sourceLabel }));
        setLabel('[data-action="move-all-left"]', t('mj.transferList.moveAllTo', { label: sourceLabel }));

        const sourceFilter = this.$('[data-role="source-filter"]');
        const targetFilter = this.$('[data-role="target-filter"]');
        if (sourceFilter != null) {
            sourceFilter.placeholder = t('mj.transferList.filterPlaceholder', { label: sourceLabel.toLowerCase() });
            sourceFilter.setAttribute('aria-label', t('mj.transferList.filterLabel', { label: sourceLabel }));
        }
        if (targetFilter != null) {
            targetFilter.placeholder = t('mj.transferList.filterPlaceholder', { label: targetLabel.toLowerCase() });
            targetFilter.setAttribute('aria-label', t('mj.transferList.filterLabel', { label: targetLabel }));
        }
    }

    /* Show or hide the optional parts; nothing is rebuilt, so no state is lost. */
    _applyStructure() {
        const searchable = this.hasAttribute('searchable');
        const reorder = this.hasAttribute('reorder');

        const sides = ['source', 'target'];
        sides.forEach((side) => {
            const search = this.$(`[part="${side}-search"]`);
            if (search == null) {
                return;
            }
            search.hidden = searchable === false;
            if (searchable === false) {
                /* A hidden filter must not keep hiding items. */
                const filterInput = this.$(`[data-role="${side}-filter"]`);
                filterInput.value = '';
                if (side === 'source') {
                    this._sourceFilter = '';
                } else {
                    this._targetFilter = '';
                }
            }
        });

        const moveUp = this.$('[data-action="move-up"]');
        const moveDown = this.$('[data-action="move-down"]');
        if (moveUp != null) {
            moveUp.hidden = reorder === false;
        }
        if (moveDown != null) {
            moveDown.hidden = reorder === false;
        }
    }

    /* A disabled list has no tab stops and announces itself as disabled. */
    _applyDisabledState() {
        const disabled = this._isDisabled();

        const sides = ['source', 'target'];
        sides.forEach((side) => {
            const lb = this.$(`[part="${side}-listbox"]`);
            const filterInput = this.$(`[data-role="${side}-filter"]`);
            if (lb != null) {
                lb.tabIndex = disabled === true ? -1 : 0;
                if (disabled === true) {
                    lb.setAttribute('aria-disabled', 'true');
                } else {
                    lb.removeAttribute('aria-disabled');
                }
            }
            if (filterInput != null) {
                filterInput.disabled = disabled;
            }
        });
    }

    _renderLists() {
        this._renderList('source');
        this._renderList('target');
        this._updateCounts();
        this._updateButtons();
    }

    _visibleItems(side) {
        const items = side === 'source' ? this._sourceItems : this._targetItems;
        const filter = side === 'source' ? this._sourceFilter : this._targetFilter;
        const needle = filter.toLowerCase();

        const visible = needle.length > 0
            ? items.filter((i) => i.label.toLowerCase().includes(needle))
            : items;
        return visible;
    }

    _renderList(side) {
        const lb = this.$(`[part="${side}-listbox"]`);
        const emptyEl = this.$(`[part="empty-${side}"]`);
        if (lb == null) {
            return;
        }

        const selected = side === 'source' ? this._sourceSelected : this._targetSelected;
        const filtered = this._visibleItems(side);

        if (emptyEl != null) {
            emptyEl.hidden = filtered.length > 0;
        }

        /* The active option must be one that is shown. */
        const activeShown = filtered.some((i) => i.value === this._active[side]);
        if (activeShown === false) {
            this._active[side] = null;
        }

        /*
         * Rebuild the rows only when the shown items differ from the ones
         * they were built for. Replacing the rows on every state change would
         * swap the node under a pointer press: focusing the listbox on
         * mousedown re-rendered it, the mouseup landed on a new node and the
         * browser dispatched no click, so the first click selected nothing.
         */
        const signature = JSON.stringify(filtered.map((item) => [item.value, item.label, item.icon, item.disabled === true]));
        const rendered = this._renderedRows[side];
        const upToDate = rendered !== null && rendered.listbox === lb && rendered.signature === signature;

        if (upToDate === false) {
            const rows = filtered.map((item, idx) => {
                const optId = `${this._optionIdPrefix}-${side}-${idx}`;
                const iconHtml = item.icon != null ? html`<span class="option-icon" aria-hidden="true">${item.icon}</span>` : '';

                return html`
                    <div
                        class="list-option"
                        role="option"
                        id="${optId}"
                        data-value="${item.value}"
                        data-index="${idx}"
                        aria-selected="false"
                        aria-disabled="${item.disabled === true ? 'true' : 'false'}"
                    >
                        ${iconHtml}
                        <span>${item.label}</span>
                    </div>
                `;
            });

            lb.innerHTML = String(html`${rows}`);
            this._renderedRows[side] = { listbox: lb, signature: signature };
        }

        /* Selection and the active option, on the rows in place. */
        let activeId = null;
        lb.querySelectorAll('.list-option').forEach((row, idx) => {
            const item = filtered[idx];
            const isSelected = item !== undefined && selected.has(item.value);
            const isActive = item !== undefined && this._active[side] === item.value;
            row.setAttribute('aria-selected', isSelected ? 'true' : 'false');
            row.classList.toggle('active', isActive);
            if (isActive) {
                activeId = row.id;
            }
        });

        if (activeId !== null) {
            lb.setAttribute('aria-activedescendant', activeId);
        } else {
            lb.removeAttribute('aria-activedescendant');
        }
    }

    /* Make `value` the keyboard-active option of a listbox and keep it in view. */
    _setActive(side, value) {
        this._active[side] = value;
        this._renderList(side);

        const lb = this.$(`[part="${side}-listbox"]`);
        const activeEl = lb != null ? lb.querySelector('.list-option.active') : null;
        if (activeEl != null && typeof activeEl.scrollIntoView === 'function') {
            activeEl.scrollIntoView({ block: 'nearest' });
        }
    }

    /* A listbox that gains focus without an active option takes its first usable one. */
    _onListFocus(side) {
        if (this._active[side] !== null) {
            return;
        }
        const selected = side === 'source' ? this._sourceSelected : this._targetSelected;
        const enabled = this._visibleItems(side).filter((i) => i.disabled !== true);
        if (enabled.length === 0) {
            return;
        }
        const firstSelected = enabled.find((i) => selected.has(i.value));
        const start = firstSelected !== undefined ? firstSelected : enabled[0];
        this._setActive(side, start.value);
    }

    _onListClick(e, side) {
        if (this._isDisabled() === true) {
            return;
        }
        const optEl = e.target.closest('.list-option');
        if (optEl == null) {
            return;
        }
        if (optEl.getAttribute('aria-disabled') === 'true') {
            return;
        }

        const value = optEl.dataset.value;
        const selected = side === 'source' ? this._sourceSelected : this._targetSelected;

        if (e.ctrlKey || e.metaKey) {
            if (selected.has(value)) {
                selected.delete(value);
            } else {
                selected.add(value);
            }
            this._anchor[side] = value;
        } else if (e.shiftKey) {
            this._selectRange(side, value);
        } else {
            selected.clear();
            selected.add(value);
            this._anchor[side] = value;
        }

        /* The listbox itself holds focus, so rebuilding its options keeps it. */
        this._setActive(side, value);
        this._updateButtons();
    }

    _onListKeydown(e, side) {
        if (this._isDisabled() === true) {
            return;
        }

        const selected = side === 'source' ? this._sourceSelected : this._targetSelected;
        const enabled = this._visibleItems(side).filter((i) => i.disabled !== true);
        const activeIdx = enabled.findIndex((i) => i.value === this._active[side]);
        const withCtrl = e.ctrlKey === true || e.metaKey === true;

        /* Ctrl shortcuts first: the plain arrow branches below would swallow them. */
        if (withCtrl && e.key === 'ArrowRight' && side === 'source') {
            e.preventDefault();
            this._moveSelectedToTarget('keyboard');
            return;
        }
        if (withCtrl && e.key === 'ArrowLeft' && side === 'target') {
            e.preventDefault();
            this._moveSelectedToSource('keyboard');
            return;
        }
        if (withCtrl && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
            e.preventDefault();
            if (side === 'target' && this.hasAttribute('reorder') === true) {
                this._reorderTargetItem(e.key === 'ArrowUp' ? -1 : 1);
            }
            return;
        }
        if (withCtrl && (e.key === 'a' || e.key === 'A')) {
            e.preventDefault();
            enabled.forEach((i) => selected.add(i.value));
            this._renderList(side);
            this._updateButtons();
            return;
        }

        let nextIdx = -1;
        if (e.key === 'ArrowDown') {
            nextIdx = Math.min(activeIdx + 1, enabled.length - 1);
        } else if (e.key === 'ArrowUp') {
            nextIdx = activeIdx < 0 ? 0 : Math.max(activeIdx - 1, 0);
        } else if (e.key === 'Home') {
            nextIdx = 0;
        } else if (e.key === 'End') {
            nextIdx = enabled.length - 1;
        }

        if (nextIdx >= 0 && nextIdx < enabled.length) {
            e.preventDefault();
            const value = enabled[nextIdx].value;
            if (e.shiftKey === true) {
                selected.add(value);
            } else {
                selected.clear();
                selected.add(value);
                this._anchor[side] = value;
            }
            this._setActive(side, value);
            this._updateButtons();
            return;
        }

        if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            if (activeIdx >= 0) {
                const value = enabled[activeIdx].value;
                if (selected.has(value)) {
                    selected.delete(value);
                } else {
                    selected.add(value);
                }
                this._anchor[side] = value;
                this._renderList(side);
                this._updateButtons();
            }
            return;
        }
    }

    _selectRange(side, endValue) {
        const items = this._visibleItems(side);
        const selected = side === 'source' ? this._sourceSelected : this._targetSelected;

        const anchorValue = this._anchor[side];
        const startIdx = anchorValue !== null ? items.findIndex((i) => i.value === anchorValue) : 0;
        const endIdx = items.findIndex((i) => i.value === endValue);

        if (startIdx < 0 || endIdx < 0) {
            selected.add(endValue);
            return;
        }

        const lo = Math.min(startIdx, endIdx);
        const hi = Math.max(startIdx, endIdx);
        items.slice(lo, hi + 1).forEach((item) => {
            if (item.disabled !== true) {
                selected.add(item.value);
            }
        });
    }

    _onControlClick(e) {
        if (this._isDisabled() === true) {
            return;
        }
        const btn = e.target.closest('button[data-action]');
        if (btn == null || btn.disabled) {
            return;
        }
        const action = btn.dataset.action;

        if (action === 'move-right') {
            this._moveSelectedToTarget('button');
        } else if (action === 'move-all-right') {
            this._moveAllToTarget();
        } else if (action === 'move-left') {
            this._moveSelectedToSource('button');
        } else if (action === 'move-all-left') {
            this._moveAllToSource();
        } else if (action === 'move-up') {
            this._reorderTargetItem(-1);
        } else if (action === 'move-down') {
            this._reorderTargetItem(1);
        }
    }

    /* ----- public move API (for custom content in the `controls` slot) ----- */

    /* Move the highlighted items: direction is "to-target" or "to-source". */
    moveSelected(direction) {
        if (direction === 'to-source') {
            this._moveSelectedToSource('api');
        } else {
            this._moveSelectedToTarget('api');
        }
    }

    /* Move every enabled item: direction is "to-target" or "to-source". */
    moveAll(direction) {
        if (direction === 'to-source') {
            this._moveAllToSource();
        } else {
            this._moveAllToTarget();
        }
    }

    /*
     * Move `items` from one pool to the other. Returns true when they moved;
     * false when the target limit would be exceeded or a `mj-move` listener
     * cancelled the move.
     */
    _moveItems(items, direction) {
        if (this._isDisabled() === true || items.length === 0) {
            return false;
        }

        if (direction === 'to-target') {
            const maxTarget = parseInt(this.getAttribute('max-target') || '0', 10);
            if (maxTarget > 0 && this._targetItems.length + items.length > maxTarget) {
                announce(t('mj.transferList.maxReached', { count: maxTarget, label: this._targetLabel() }), 'polite');
                return false;
            }
        }

        const proceed = this.emit('mj-move', { items, direction }, { cancelable: true });
        if (proceed === false) {
            return false;
        }

        const movedValues = new Set(items.map((i) => i.value));
        if (direction === 'to-target') {
            this._sourceItems = this._sourceItems.filter((i) => !movedValues.has(i.value));
            this._targetItems = [...this._targetItems, ...items];
            this._sourceSelected.clear();
        } else {
            this._targetItems = this._targetItems.filter((i) => !movedValues.has(i.value));
            this._sourceItems = [...this._sourceItems, ...items];
            this._targetSelected.clear();
        }

        /* The user decided where things go; late options no longer follow `value`. */
        this._wantedTargetValues = [];
        this._pruneSelection();
        this._renderLists();
        this._syncFormValue();
        this._announceMove(items.length, direction);
        this._emitChange();
        return true;
    }

    /*
     * After a move the button that triggered it is usually disabled (the
     * selection is gone), which would drop focus to the document. Focus goes
     * to the listbox that received the items, on the first moved item. A
     * keyboard move from inside a listbox keeps focus where it is.
     */
    _focusAfterMove(items, direction, origin) {
        if (origin !== 'button') {
            return;
        }
        const side = direction === 'to-target' ? 'target' : 'source';
        const lb = this.$(`[part="${side}-listbox"]`);
        if (lb == null) {
            return;
        }
        this._setActive(side, items[0].value);
        lb.focus();
    }

    _moveSelectedToTarget(origin) {
        const items = this._sourceItems.filter((i) => this._sourceSelected.has(i.value) && i.disabled !== true);
        const moved = this._moveItems(items, 'to-target');
        if (moved === true) {
            this._focusAfterMove(items, 'to-target', origin);
        }
    }

    _moveAllToTarget() {
        const items = this._sourceItems.filter((i) => i.disabled !== true);
        const moved = this._moveItems(items, 'to-target');
        if (moved === true) {
            this._focusAfterMove(items, 'to-target', 'button');
        }
    }

    _moveSelectedToSource(origin) {
        const items = this._targetItems.filter((i) => this._targetSelected.has(i.value) && i.disabled !== true);
        const moved = this._moveItems(items, 'to-source');
        if (moved === true) {
            this._focusAfterMove(items, 'to-source', origin);
        }
    }

    _moveAllToSource() {
        const items = this._targetItems.filter((i) => i.disabled !== true);
        const moved = this._moveItems(items, 'to-source');
        if (moved === true) {
            this._focusAfterMove(items, 'to-source', 'button');
        }
    }

    _reorderTargetItem(delta) {
        if (this._isDisabled() === true || this._targetSelected.size !== 1) {
            return;
        }
        const value = Array.from(this._targetSelected)[0];
        const currentIdx = this._targetItems.findIndex((i) => i.value === value);
        if (currentIdx < 0) {
            return;
        }
        const newIdx = currentIdx + delta;
        if (newIdx < 0 || newIdx >= this._targetItems.length) {
            return;
        }

        const item = this._targetItems[currentIdx];
        const newItems = this._targetItems.slice();
        newItems.splice(currentIdx, 1);
        newItems.splice(newIdx, 0, item);

        this._targetItems = newItems;
        this._wantedTargetValues = [];
        this._setActive('target', value);
        this._updateButtons();
        this._syncFormValue();

        this.emit('mj-reorder', { item, fromIndex: currentIdx, toIndex: newIdx });
        this._emitChange();
    }

    _announceMove(count, direction) {
        const sourceLabel = this._sourceLabel();
        const targetLabel = this._targetLabel();
        const dest = direction === 'to-target' ? targetLabel : sourceLabel;
        const destCount = direction === 'to-target' ? this._targetItems.length : this._sourceItems.length;
        const moved = t('mj.transferList.moved', { count: count, label: dest });
        const contains = t('mj.transferList.contains', { count: destCount, label: dest });
        const msg = `${moved} ${contains}`;
        announce(msg, 'polite');
    }

    _updateCounts() {
        const sourceCountEl = this.$('[data-count="source"]');
        const targetCountEl = this.$('[data-count="target"]');
        if (sourceCountEl != null) {
            sourceCountEl.textContent = t('mj.transferList.count', { count: this._sourceItems.length });
        }
        if (targetCountEl != null) {
            targetCountEl.textContent = t('mj.transferList.count', { count: this._targetItems.length });
        }
    }

    _updateButtons() {
        const disabled = this._isDisabled();
        const maxTarget = parseInt(this.getAttribute('max-target') || '0', 10);
        const atMax = maxTarget > 0 && this._targetItems.length >= maxTarget;

        const moveRight = this.$('[data-action="move-right"]');
        const moveAllRight = this.$('[data-action="move-all-right"]');
        const moveLeft = this.$('[data-action="move-left"]');
        const moveAllLeft = this.$('[data-action="move-all-left"]');
        const moveUp = this.$('[data-action="move-up"]');
        const moveDown = this.$('[data-action="move-down"]');

        const hasSourceSelection = this._sourceSelected.size > 0;
        const hasTargetSelection = this._targetSelected.size > 0;
        const hasSource = this._sourceItems.some((i) => i.disabled !== true);
        const hasTarget = this._targetItems.some((i) => i.disabled !== true);

        if (moveRight != null) {
            moveRight.disabled = disabled || !hasSourceSelection || atMax;
        }
        if (moveAllRight != null) {
            moveAllRight.disabled = disabled || !hasSource || atMax;
        }
        if (moveLeft != null) {
            moveLeft.disabled = disabled || !hasTargetSelection;
        }
        if (moveAllLeft != null) {
            moveAllLeft.disabled = disabled || !hasTarget;
        }

        let selectedIdx = -1;
        if (this._targetSelected.size === 1) {
            const value = Array.from(this._targetSelected)[0];
            selectedIdx = this._targetItems.findIndex((i) => i.value === value);
        }
        if (moveUp != null) {
            moveUp.disabled = disabled || selectedIdx <= 0;
        }
        if (moveDown != null) {
            moveDown.disabled = disabled || selectedIdx < 0 || selectedIdx >= this._targetItems.length - 1;
        }
    }

    _emitChange() {
        const targetValues = this._targetItems.map((i) => i.value);
        const sourceValues = this._sourceItems.map((i) => i.value);
        this.emit('mj-change', { targetValues, sourceValues });
    }

    /*
     * Submit one `name=value` entry per target item, in display order.
     * `_value` holds the joined string so the mixin's `required` check sees an
     * empty target as empty.
     */
    _syncFormValue() {
        const joined = this._targetItems.map((i) => i.value).join(',');
        const name = this.getAttribute('name') || '';

        this._value = joined;
        if (this._internals != null) {
            const fd = new FormData();
            if (name.length > 0) {
                this._targetItems.forEach((i) => fd.append(name, i.value));
            }
            this._internals.setFormValue(fd, joined);
        }
        this._refreshValidity();
        this._updateCounts();
        this._updateButtons();
    }

    /* Reset returns every item to its initial side and order. */
    formResetCallback() {
        this._resetPools();
    }

    formStateRestoreCallback(state) {
        if (typeof state === 'string') {
            this._applyValueString(state);
        }
    }
}
