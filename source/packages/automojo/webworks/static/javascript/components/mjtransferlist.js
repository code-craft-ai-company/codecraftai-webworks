import { MjElement, nextId } from '../core/mjelement.js';
import { FormControlMixin } from '../core/forminternals.js';
import { announce } from '../core/announcer.js';

export class MjTransferList extends FormControlMixin(MjElement) {
    static tagName = 'mj-transfer-list';

    static styles = `
        :host {
            display: block;
            font-family: var(--mj-font-family-base);
            font-size: var(--mj-font-size-md);
        }
        :host([disabled]) {
            opacity: var(--mj-opacity-disabled);
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
            border: var(--mj-border-width-sm) solid var(--mj-color-border-default);
            border-radius: var(--mj-transfer-list-border-radius, var(--mj-radius-md));
            overflow: hidden;
        }
        [part="source-header"],
        [part="target-header"] {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: var(--mj-space-2) var(--mj-space-3);
            background: var(--mj-color-surface-subtle);
            border-bottom: var(--mj-border-width-sm) solid var(--mj-color-border-default);
            font-weight: var(--mj-font-weight-semibold);
            font-size: var(--mj-font-size-sm);
        }
        .pane-count {
            color: var(--mj-color-text-subtle);
            font-weight: var(--mj-font-weight-regular);
        }
        [part="source-search"],
        [part="target-search"] {
            padding: var(--mj-space-2) var(--mj-space-3);
            border-bottom: var(--mj-border-width-sm) solid var(--mj-color-border-default);
        }
        [part="source-search"] input,
        [part="target-search"] input {
            width: 100%;
            padding: var(--mj-space-1) var(--mj-space-2);
            border: var(--mj-border-width-sm) solid var(--mj-color-border-default);
            border-radius: var(--mj-radius-sm);
            background: var(--mj-color-surface-default);
            font-family: inherit;
            font-size: var(--mj-font-size-sm);
            color: var(--mj-color-text-default);
            outline: none;
        }
        [part="source-search"] input:focus,
        [part="target-search"] input:focus {
            border-color: var(--mj-color-border-focus);
            outline: var(--mj-border-width-md) solid var(--mj-color-focus-ring);
            outline-offset: 1px;
        }
        [part="source-listbox"],
        [part="target-listbox"] {
            flex: 1;
            overflow-y: auto;
            height: var(--mj-transfer-list-pane-height, 16rem);
            padding: var(--mj-space-1);
        }
        .list-option {
            display: flex;
            align-items: center;
            gap: var(--mj-space-2);
            padding: var(--mj-space-2) var(--mj-space-3);
            border-radius: var(--mj-radius-sm);
            cursor: pointer;
            user-select: none;
        }
        .list-option:hover {
            background: var(--mj-color-surface-hover);
        }
        .list-option[aria-selected="true"] {
            background: var(--mj-color-selected-subtle);
        }
        .list-option:focus-visible {
            outline: var(--mj-border-width-md) solid var(--mj-color-focus-ring);
            outline-offset: -2px;
        }
        .list-option[aria-disabled="true"] {
            opacity: var(--mj-opacity-disabled);
            cursor: not-allowed;
        }
        .option-icon {
            width: 1rem;
            height: 1rem;
            flex-shrink: 0;
            color: var(--mj-color-text-subtle);
        }
        [part="empty-source"],
        [part="empty-target"] {
            padding: var(--mj-space-4);
            text-align: center;
            color: var(--mj-color-text-subtle);
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
            background: var(--mj-color-surface-default);
            border: var(--mj-border-width-sm) solid var(--mj-color-border-default);
            border-radius: var(--mj-radius-sm);
            cursor: pointer;
            color: var(--mj-color-text-default);
            transition: background var(--mj-motion-duration-fast) var(--mj-motion-easing-default),
                        border-color var(--mj-motion-duration-fast) var(--mj-motion-easing-default);
        }
        [part="controls"] button:hover:not(:disabled) {
            background: var(--mj-color-surface-hover);
            border-color: var(--mj-color-border-strong);
        }
        [part="controls"] button:focus-visible {
            outline: var(--mj-border-width-md) solid var(--mj-color-focus-ring);
            outline-offset: 2px;
        }
        [part="controls"] button:disabled {
            opacity: var(--mj-opacity-disabled);
            cursor: not-allowed;
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

    render() {
        const sourceLabel = this.getAttribute('source-label') || 'Available';
        const targetLabel = this.getAttribute('target-label') || 'Selected';
        const searchable = this.hasAttribute('searchable');
        const reorder = this.hasAttribute('reorder');

        return `
            <div part="container">
                <div part="source-pane" role="region" aria-labelledby="${this._srcHeaderId}">
                    <div part="source-header" id="${this._srcHeaderId}">
                        <span>${sourceLabel}</span>
                        <span class="pane-count" aria-live="polite" aria-atomic="true">
                            <span data-count="source">0</span> items
                        </span>
                    </div>
                    ${searchable ? `
                    <div part="source-search">
                        <input
                            type="search"
                            placeholder="Filter ${sourceLabel.toLowerCase()}…"
                            aria-label="Filter ${sourceLabel}"
                            data-role="source-filter"
                        >
                    </div>` : ''}
                    <div
                        part="source-listbox"
                        role="listbox"
                        aria-multiselectable="true"
                        aria-label="${sourceLabel}"
                        tabindex="0"
                        data-list="source"
                    ></div>
                    <div part="empty-source" hidden>
                        <slot name="empty-source">No available items.</slot>
                    </div>
                </div>

                <div part="controls" role="group" aria-label="Move controls">
                    <button
                        part="move-right"
                        type="button"
                        aria-label="Move selected to ${targetLabel}"
                        data-action="move-right"
                        disabled
                    >›</button>
                    <button
                        part="move-all-right"
                        type="button"
                        aria-label="Move all to ${targetLabel}"
                        data-action="move-all-right"
                        disabled
                    >»</button>
                    <button
                        part="move-left"
                        type="button"
                        aria-label="Move selected to ${sourceLabel}"
                        data-action="move-left"
                        disabled
                    >‹</button>
                    <button
                        part="move-all-left"
                        type="button"
                        aria-label="Move all to ${sourceLabel}"
                        data-action="move-all-left"
                        disabled
                    >«</button>
                    ${reorder ? `
                    <button
                        part="move-up"
                        type="button"
                        aria-label="Move up"
                        data-action="move-up"
                        disabled
                    >↑</button>
                    <button
                        part="move-down"
                        type="button"
                        aria-label="Move down"
                        data-action="move-down"
                        disabled
                    >↓</button>` : ''}
                </div>

                <div part="target-pane" role="region" aria-labelledby="${this._tgtHeaderId}">
                    <div part="target-header" id="${this._tgtHeaderId}">
                        <span>${targetLabel}</span>
                        <span class="pane-count" aria-live="polite" aria-atomic="true">
                            <span data-count="target">0</span> items
                        </span>
                    </div>
                    ${searchable ? `
                    <div part="target-search">
                        <input
                            type="search"
                            placeholder="Filter ${targetLabel.toLowerCase()}…"
                            aria-label="Filter ${targetLabel}"
                            data-role="target-filter"
                        >
                    </div>` : ''}
                    <div
                        part="target-listbox"
                        role="listbox"
                        aria-multiselectable="true"
                        aria-label="${targetLabel}"
                        tabindex="0"
                        data-list="target"
                    ></div>
                    <div part="empty-target" hidden>
                        <slot name="empty-target">No selected items.</slot>
                    </div>
                </div>
            </div>
            <div id="${this._liveId}" aria-live="polite" aria-atomic="true" class="sr-only"></div>
        `;
    }

    afterRender() {
        // Read initial items from slotted mj-option elements
        this._initFromSlot();

        // Wire control buttons
        const controls = this.$('[part="controls"]');
        if (controls != null) {
            this.listen(controls, 'click', (e) => this._onControlClick(e));
        }

        // Wire listbox clicks
        const sourceLb = this.$('[part="source-listbox"]');
        const targetLb = this.$('[part="target-listbox"]');

        if (sourceLb != null) {
            this.listen(sourceLb, 'click', (e) => this._onListClick(e, 'source'));
            this.listen(sourceLb, 'keydown', (e) => this._onListKeydown(e, 'source'));
        }
        if (targetLb != null) {
            this.listen(targetLb, 'click', (e) => this._onListClick(e, 'target'));
            this.listen(targetLb, 'keydown', (e) => this._onListKeydown(e, 'target'));
        }

        // Wire search inputs
        const sourceFilter = this.$('[data-role="source-filter"]');
        const targetFilter = this.$('[data-role="target-filter"]');
        if (sourceFilter != null) {
            this.listen(sourceFilter, 'input', (e) => {
                this._sourceFilter = e.currentTarget.value;
                this._renderList('source');
            });
        }
        if (targetFilter != null) {
            this.listen(targetFilter, 'input', (e) => {
                this._targetFilter = e.currentTarget.value;
                this._renderList('target');
            });
        }

        // Observe slot changes
        const slot = this.shadowRoot != null ? this.shadowRoot.querySelector('slot:not([name])') : null;
        if (slot != null) {
            this.listen(slot, 'slotchange', () => this._initFromSlot());
        }

        this._renderLists();
        this._syncFormValue();
    }

    onAttributeChanged(name, oldVal, newVal) {
        if (name === 'value') {
            // Sync target items from value attribute
            const targetValues = new Set((newVal || '').split(',').map((v) => v.trim()).filter((v) => v.length > 0));
            if (targetValues.size > 0) {
                const allItems = this.allItems;
                this._sourceItems = allItems.filter((i) => !targetValues.has(i.value));
                this._targetItems = allItems.filter((i) => targetValues.has(i.value));
                this._renderLists();
                this._syncFormValue();
            }
        }
        if (name === 'source-label' || name === 'target-label' || name === 'searchable' ||
            name === 'reorder' || name === 'orientation') {
            // Full re-render needed for structural changes
            this._rerender();
        }
    }

    _rerender() {
        const sourceItems = this._sourceItems.slice();
        const targetItems = this._targetItems.slice();
        // Re-render shadow DOM
        const root = this.shadowRoot;
        if (root == null) {
            return;
        }
        // Re-invoke render
        const container = this.$('[part="container"]');
        if (container != null) {
            container.remove();
        }
        const live = this.$(`#${this._liveId}`);
        if (live != null) {
            live.remove();
        }
        // Re-apply render output
        const tmp = document.createElement('div');
        tmp.innerHTML = this.render();
        while (tmp.firstChild != null) {
            root.appendChild(tmp.firstChild);
        }
        this._sourceItems = sourceItems;
        this._targetItems = targetItems;
        this.afterRender();
    }

    _initFromSlot() {
        const options = this.querySelectorAll('mj-option');
        const newSource = [];
        const newTarget = [];

        options.forEach((opt) => {
            const value = opt.getAttribute('value') || opt.textContent.trim();
            const label = opt.textContent.trim();
            const icon = opt.getAttribute('icon') || null;
            const disabled = opt.hasAttribute('disabled');
            const selected = opt.hasAttribute('selected');
            const item = { value, label, icon, disabled };

            if (selected) {
                newTarget.push(item);
            } else {
                newSource.push(item);
            }
        });

        // Only update if we actually have slotted items
        if (options.length > 0) {
            this._sourceItems = newSource;
            this._targetItems = newTarget;
            this._renderLists();
            this._syncFormValue();
        }
    }

    _renderLists() {
        this._renderList('source');
        this._renderList('target');
        this._updateCounts();
        this._updateButtons();
    }

    _renderList(side) {
        const lb = this.$(`[part="${side}-listbox"]`);
        const emptyEl = this.$(`[part="empty-${side}"]`);
        if (lb == null) {
            return;
        }

        const items = side === 'source' ? this._sourceItems : this._targetItems;
        const selected = side === 'source' ? this._sourceSelected : this._targetSelected;
        const filter = side === 'source' ? this._sourceFilter : this._targetFilter;

        const filtered = filter.length > 0
            ? items.filter((i) => i.label.toLowerCase().includes(filter.toLowerCase()))
            : items;

        if (emptyEl != null) {
            emptyEl.hidden = filtered.length > 0;
        }

        if (filtered.length === 0) {
            lb.innerHTML = '';
            return;
        }

        const html = filtered.map((item, idx) => {
            const isSelected = selected.has(item.value);
            const optId = nextId('mj-tl-opt');
            const iconHtml = item.icon != null ? `<span class="option-icon" aria-hidden="true">${item.icon}</span>` : '';

            return `
                <div
                    class="list-option"
                    role="option"
                    id="${optId}"
                    data-value="${item.value}"
                    data-index="${idx}"
                    aria-selected="${isSelected ? 'true' : 'false'}"
                    ${item.disabled === true ? 'aria-disabled="true"' : ''}
                    tabindex="-1"
                >
                    ${iconHtml}
                    <span>${item.label}</span>
                </div>
            `;
        });

        lb.innerHTML = html.join('');
    }

    _onListClick(e, side) {
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
        } else if (e.shiftKey) {
            this._selectRange(side, value);
        } else {
            selected.clear();
            selected.add(value);
        }

        this._renderList(side);
        this._updateButtons();
        optEl.focus();
    }

    _onListKeydown(e, side) {
        const lb = this.$(`[part="${side}-listbox"]`);
        if (lb == null) {
            return;
        }
        const opts = Array.from(lb.querySelectorAll('.list-option:not([aria-disabled="true"])'));
        const focused = lb.querySelector('.list-option:focus');
        const focusIdx = focused != null ? opts.indexOf(focused) : -1;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            const nextIdx = Math.min(focusIdx + 1, opts.length - 1);
            if (opts[nextIdx] != null) {
                opts[nextIdx].focus();
                if (!e.shiftKey) {
                    const selected = side === 'source' ? this._sourceSelected : this._targetSelected;
                    selected.clear();
                    selected.add(opts[nextIdx].dataset.value);
                } else {
                    const selected = side === 'source' ? this._sourceSelected : this._targetSelected;
                    selected.add(opts[nextIdx].dataset.value);
                }
                this._renderList(side);
                this._updateButtons();
                opts[nextIdx].focus();
            }
            return;
        }

        if (e.key === 'ArrowUp') {
            e.preventDefault();
            const prevIdx = Math.max(focusIdx - 1, 0);
            if (opts[prevIdx] != null) {
                opts[prevIdx].focus();
                if (!e.shiftKey) {
                    const selected = side === 'source' ? this._sourceSelected : this._targetSelected;
                    selected.clear();
                    selected.add(opts[prevIdx].dataset.value);
                } else {
                    const selected = side === 'source' ? this._sourceSelected : this._targetSelected;
                    selected.add(opts[prevIdx].dataset.value);
                }
                this._renderList(side);
                this._updateButtons();
                opts[prevIdx].focus();
            }
            return;
        }

        if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            if (focused != null) {
                const value = focused.dataset.value;
                const selected = side === 'source' ? this._sourceSelected : this._targetSelected;
                if (selected.has(value)) {
                    selected.delete(value);
                } else {
                    selected.add(value);
                }
                this._renderList(side);
                this._updateButtons();
                focused.focus();
            }
            return;
        }

        // Keyboard shortcuts: Ctrl+ArrowRight / Ctrl+ArrowLeft
        if (e.ctrlKey && e.key === 'ArrowRight' && side === 'source') {
            e.preventDefault();
            this._moveSelectedToTarget();
            return;
        }
        if (e.ctrlKey && e.key === 'ArrowLeft' && side === 'target') {
            e.preventDefault();
            this._moveSelectedToSource();
            return;
        }
        if (e.ctrlKey && e.key === 'ArrowUp' && side === 'target') {
            e.preventDefault();
            this._reorderTargetItem(-1);
            return;
        }
        if (e.ctrlKey && e.key === 'ArrowDown' && side === 'target') {
            e.preventDefault();
            this._reorderTargetItem(1);
            return;
        }

        // Home / End
        if (e.key === 'Home' && opts.length > 0) {
            e.preventDefault();
            opts[0].focus();
            return;
        }
        if (e.key === 'End' && opts.length > 0) {
            e.preventDefault();
            opts[opts.length - 1].focus();
            return;
        }
    }

    _selectRange(side, endValue) {
        const items = side === 'source' ? this._sourceItems : this._targetItems;
        const selected = side === 'source' ? this._sourceSelected : this._targetSelected;

        const lastSelected = Array.from(selected).pop();
        const startIdx = lastSelected != null ? items.findIndex((i) => i.value === lastSelected) : 0;
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
        const btn = e.target.closest('button[data-action]');
        if (btn == null || btn.disabled) {
            return;
        }
        const action = btn.dataset.action;

        if (action === 'move-right') {
            this._moveSelectedToTarget();
        } else if (action === 'move-all-right') {
            this._moveAllToTarget();
        } else if (action === 'move-left') {
            this._moveSelectedToSource();
        } else if (action === 'move-all-left') {
            this._moveAllToSource();
        } else if (action === 'move-up') {
            this._reorderTargetItem(-1);
        } else if (action === 'move-down') {
            this._reorderTargetItem(1);
        }
    }

    _moveSelectedToTarget() {
        if (this._sourceSelected.size === 0) {
            return;
        }
        const items = this._sourceItems.filter((i) => this._sourceSelected.has(i.value) && i.disabled !== true);
        if (items.length === 0) {
            return;
        }

        const maxTarget = parseInt(this.getAttribute('max-target') || '0', 10);
        if (maxTarget > 0 && this._targetItems.length + items.length > maxTarget) {
            const targetLabel = this.getAttribute('target-label') || 'Selected';
            announce(`Maximum ${maxTarget} items reached in ${targetLabel}.`, 'polite');
            return;
        }

        const moveEvent = this.emit('mj-move', { items, direction: 'to-target' }, { cancelable: true });
        if (moveEvent.defaultPrevented) {
            return;
        }

        const movedValues = new Set(items.map((i) => i.value));
        this._sourceItems = this._sourceItems.filter((i) => !movedValues.has(i.value));
        this._targetItems = [...this._targetItems, ...items];
        this._sourceSelected.clear();

        this._renderLists();
        this._syncFormValue();
        this._announceMove(items.length, 'to-target');
        this._emitChange();

        // Set focus to the listbox that received items
        const targetLb = this.$('[part="target-listbox"]');
        if (targetLb != null) {
            targetLb.focus();
        }
    }

    _moveAllToTarget() {
        const items = this._sourceItems.filter((i) => i.disabled !== true);
        if (items.length === 0) {
            return;
        }

        const maxTarget = parseInt(this.getAttribute('max-target') || '0', 10);
        if (maxTarget > 0 && this._targetItems.length + items.length > maxTarget) {
            const targetLabel = this.getAttribute('target-label') || 'Selected';
            announce(`Maximum ${maxTarget} items reached in ${targetLabel}.`, 'polite');
            return;
        }

        const moveEvent = this.emit('mj-move', { items, direction: 'to-target' }, { cancelable: true });
        if (moveEvent.defaultPrevented) {
            return;
        }

        const disabledItems = this._sourceItems.filter((i) => i.disabled === true);
        this._sourceItems = disabledItems;
        this._targetItems = [...this._targetItems, ...items];
        this._sourceSelected.clear();

        this._renderLists();
        this._syncFormValue();
        this._announceMove(items.length, 'to-target');
        this._emitChange();
    }

    _moveSelectedToSource() {
        if (this._targetSelected.size === 0) {
            return;
        }
        const items = this._targetItems.filter((i) => this._targetSelected.has(i.value) && i.disabled !== true);
        if (items.length === 0) {
            return;
        }

        const moveEvent = this.emit('mj-move', { items, direction: 'to-source' }, { cancelable: true });
        if (moveEvent.defaultPrevented) {
            return;
        }

        const movedValues = new Set(items.map((i) => i.value));
        this._targetItems = this._targetItems.filter((i) => !movedValues.has(i.value));
        this._sourceItems = [...this._sourceItems, ...items];
        this._targetSelected.clear();

        this._renderLists();
        this._syncFormValue();
        this._announceMove(items.length, 'to-source');
        this._emitChange();

        // Set focus to source listbox
        const sourceLb = this.$('[part="source-listbox"]');
        if (sourceLb != null) {
            sourceLb.focus();
        }
    }

    _moveAllToSource() {
        const items = this._targetItems.filter((i) => i.disabled !== true);
        if (items.length === 0) {
            return;
        }

        const moveEvent = this.emit('mj-move', { items, direction: 'to-source' }, { cancelable: true });
        if (moveEvent.defaultPrevented) {
            return;
        }

        const disabledItems = this._targetItems.filter((i) => i.disabled === true);
        this._targetItems = disabledItems;
        this._sourceItems = [...this._sourceItems, ...items];
        this._targetSelected.clear();

        this._renderLists();
        this._syncFormValue();
        this._announceMove(items.length, 'to-source');
        this._emitChange();
    }

    _reorderTargetItem(delta) {
        if (this._targetSelected.size !== 1) {
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
        this._renderList('target');
        this._syncFormValue();

        this.emit('mj-reorder', { item, fromIndex: currentIdx, toIndex: newIdx });

        // Re-focus the moved item
        const targetLb = this.$('[part="target-listbox"]');
        if (targetLb != null) {
            const opts = targetLb.querySelectorAll('.list-option');
            if (opts[newIdx] != null) {
                opts[newIdx].focus();
            }
        }
    }

    _announceMove(count, direction) {
        const sourceLabel = this.getAttribute('source-label') || 'Available';
        const targetLabel = this.getAttribute('target-label') || 'Selected';
        const dest = direction === 'to-target' ? targetLabel : sourceLabel;
        const destCount = direction === 'to-target' ? this._targetItems.length : this._sourceItems.length;
        const msg = `${count} item${count !== 1 ? 's' : ''} moved to ${dest}. ${dest} now contains ${destCount} item${destCount !== 1 ? 's' : ''}.`;
        announce(msg, 'polite');
    }

    _updateCounts() {
        const sourceCountEl = this.$('[data-count="source"]');
        const targetCountEl = this.$('[data-count="target"]');
        if (sourceCountEl != null) {
            sourceCountEl.textContent = String(this._sourceItems.length);
        }
        if (targetCountEl != null) {
            targetCountEl.textContent = String(this._targetItems.length);
        }
    }

    _updateButtons() {
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
            moveRight.disabled = !hasSourceSelection || atMax;
        }
        if (moveAllRight != null) {
            moveAllRight.disabled = !hasSource || atMax;
        }
        if (moveLeft != null) {
            moveLeft.disabled = !hasTargetSelection;
        }
        if (moveAllLeft != null) {
            moveAllLeft.disabled = !hasTarget;
        }

        if (moveUp != null || moveDown != null) {
            const canReorder = this._targetSelected.size === 1;
            if (moveUp != null) {
                moveUp.disabled = !canReorder;
            }
            if (moveDown != null) {
                moveDown.disabled = !canReorder;
            }
        }
    }

    _emitChange() {
        const targetValues = this._targetItems.map((i) => i.value);
        const sourceValues = this._sourceItems.map((i) => i.value);
        this.emit('mj-change', { targetValues, sourceValues });
    }

    _syncFormValue() {
        const fd = new FormData();
        const name = this.getAttribute('name') || '';
        if (name.length > 0) {
            this._targetItems.forEach((i) => fd.append(name, i.value));
        }
        this._setFormValue(fd);
        this._customValidity(this._computeValidity());
        this._updateCounts();
        this._updateButtons();
    }

    _computeValidity() {
        const required = this.hasAttribute('required');
        if (required && this._targetItems.length === 0) {
            return 'Please select at least one item.';
        }
        return '';
    }

    formResetCallback() {
        // Re-initialize from slotted options
        this._sourceSelected.clear();
        this._targetSelected.clear();
        this._initFromSlot();
        this._syncFormValue();
    }
}
