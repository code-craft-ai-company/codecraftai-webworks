import { MjElement, nextId } from '../core/mjelement.js';
import { FormControlMixin } from '../core/forminternals.js';
import { autoPosition } from '../core/overlay.js';
import { announce } from '../core/announcer.js';
import { html, safeUrl } from '../core/html.js';
import { t } from '../core/intl.js';

/*
 * mj-tag-picker -- a combobox that yields several values as removable tokens.
 *
 * State lives in `_tokens`; the token list, the input state and the form
 * value are always rebuilt from it (`_tokensChanged`). The `value` attribute
 * is the INITIAL value only: user changes are not reflected back to it, so a
 * form reset can restore what the author wrote.
 *
 * Suggestions come from, in order of precedence:
 *   dataSource   an object with `query({ filter, query, offset, limit, signal })`
 *                (the core DataSource contract, resolving to `{ items }` or an
 *                array) or the older `fetch({ query, signal })` shape
 *   src          a URL; the query is appended as `q=` and the response is a
 *                JSON array or `{ items: [...] }`
 *   <mj-option>  light-DOM children, filtered by label
 * A suggestion is a string or `{ value, label, avatar?, meta? }`.
 */
export class MjTagPicker extends FormControlMixin(MjElement) {
    static tagName = 'mj-tag-picker';

    static styles = `
        :host {
            display: block;
            font-family: var(--mj-font-sans);
            font-size: var(--mj-font-size-md);
        }
        :host([disabled]),
        :host(:disabled) {
            opacity: 0.55;
            pointer-events: none;
        }
        [part="container"] {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: var(--mj-tag-picker-token-gap, var(--mj-space-1));
            min-height: var(--mj-tag-picker-min-height, var(--mj-control-height-md));
            padding: var(--mj-space-1) var(--mj-space-2);
            border: 1px solid var(--mj-border-strong);
            border-radius: var(--mj-tag-picker-border-radius, var(--mj-radius-md));
            background: var(--mj-surface);
            color: var(--mj-text);
            cursor: text;
            transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
        }
        :host([aria-invalid="true"]) [part="container"],
        :host([invalid]) [part="container"] {
            border-color: var(--mj-color-danger);
        }
        [part="container"]:focus-within {
            border-color: var(--mj-accent);
            outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
            outline-offset: var(--mj-focus-ring-offset);
        }
        [part="token-list"] {
            display: contents;
        }
        [part="token"] {
            display: inline-flex;
            align-items: center;
            gap: var(--mj-space-1);
            padding-block: 0;
            padding-inline: var(--mj-space-2) var(--mj-space-1);
            height: 1.625rem;
            background: var(--mj-tag-picker-token-bg, var(--mj-bg-muted));
            border: 1px solid var(--mj-border);
            border-radius: var(--mj-tag-picker-token-radius, var(--mj-radius-pill));
            font-size: var(--mj-font-size-sm);
            white-space: nowrap;
        }
        [part="token-avatar"] {
            width: var(--mj-tag-picker-avatar-size, 1.25rem);
            height: var(--mj-tag-picker-avatar-size, 1.25rem);
            border-radius: var(--mj-radius-circle);
            object-fit: cover;
            flex-shrink: 0;
        }
        [part="token-avatar"].initials,
        [part="option-avatar"].initials {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--mj-accent);
            color: var(--mj-text-on-accent);
            font-size: 0.625rem;
            font-weight: var(--mj-font-weight-bold);
        }
        [part="token-remove"] {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.25rem;
            height: 1.25rem;
            padding: 0;
            margin: 0;
            background: none;
            border: none;
            cursor: pointer;
            font: inherit;
            line-height: 1;
            color: var(--mj-text-muted);
            border-radius: var(--mj-radius-circle);
            position: relative;
        }
        /* Enlarges the pointer target to the minimum size without growing the chip. */
        [part="token-remove"]::after {
            content: "";
            position: absolute;
            inset-block: calc((1.25rem - var(--mj-target-min)) / 2);
            inset-inline: -0.25rem;
        }
        [part="token-remove"]:hover {
            color: var(--mj-text);
            background: var(--mj-border);
        }
        [part="token-remove"]:focus-visible {
            outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
            outline-offset: 1px;
        }
        [part="token-remove"]:disabled {
            cursor: not-allowed;
        }
        [part="input"] {
            flex: 1;
            min-width: 8rem;
            height: 1.625rem;
            border: none;
            background: transparent;
            font-family: inherit;
            font-size: inherit;
            color: var(--mj-text);
            outline: none;
        }
        [part="input"]::placeholder {
            color: var(--mj-text-muted);
        }
        [part="input"]:disabled {
            pointer-events: none;
        }
        [part="popup"] {
            position: fixed;
            z-index: var(--mj-layer-popover);
            background: var(--mj-surface-raised);
            color: var(--mj-text);
            border: 1px solid var(--mj-border);
            border-radius: var(--mj-radius-md);
            box-shadow: var(--mj-elevation-2);
            overflow: hidden;
        }
        [part="popup"][hidden] {
            display: none;
        }
        [part="listbox"] {
            max-height: var(--mj-tag-picker-popup-max-height, 16rem);
            overflow-y: auto;
            padding: var(--mj-space-1);
        }
        [part="option"] {
            display: flex;
            align-items: center;
            gap: var(--mj-space-2);
            padding: var(--mj-space-2) var(--mj-space-3);
            border-radius: var(--mj-radius-sm);
            cursor: pointer;
            user-select: none;
        }
        [part="option"]:hover,
        [part="option"][aria-selected="true"] {
            background: var(--mj-bg-subtle);
        }
        [part="option"].active {
            background: var(--mj-bg-muted);
            outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
            outline-offset: -2px;
        }
        [part="option"].already-selected {
            opacity: 0.5;
            cursor: default;
        }
        [part="option-avatar"] {
            width: var(--mj-tag-picker-avatar-size, 1.25rem);
            height: var(--mj-tag-picker-avatar-size, 1.25rem);
            border-radius: var(--mj-radius-circle);
            object-fit: cover;
            flex-shrink: 0;
        }
        [part="option-label"] {
            flex: 1;
        }
        [part="option-meta"] {
            font-size: var(--mj-font-size-sm);
            color: var(--mj-text-muted);
        }
        [part="option-label"] mark {
            background: var(--mj-color-warning-surface);
            color: inherit;
            font-weight: var(--mj-font-weight-bold);
            border-radius: 2px;
        }
        [part="no-results"],
        [part="loading"] {
            padding: var(--mj-space-3);
            text-align: center;
            color: var(--mj-text-muted);
            font-size: var(--mj-font-size-sm);
        }
        [part="max-count"] {
            padding-block-start: var(--mj-space-1);
            color: var(--mj-text-muted);
            font-size: var(--mj-font-size-sm);
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

    static watched = ['name', 'value', 'type', 'placeholder', 'disabled', 'readonly',
        'required', 'free-text', 'max-count', 'debounce', 'min-chars', 'src',
        'duplicate-values', 'delimiter', 'aria-label'];

    constructor() {
        super();
        this._initFormControl();

        this._tokens = [];
        this._suggestions = [];
        this._activeIndex = -1;
        this._open = false;
        this._debounceTimer = null;
        this._disposePosition = null;
        this._dataSource = null;
        this._inputId = nextId('mj-tp-input');
        this._listboxId = nextId('mj-tp-lb');
        this._liveId = nextId('mj-tp-live');
        this._maxCountId = nextId('mj-tp-max');
        this._abortController = null;

        /* True while an ancestor <fieldset disabled> disables the control. */
        this._formDisabled = false;

        /* Incremented for every suggestion request; a stale response is dropped. */
        this._requestSeq = 0;

        /* True when the `value` attribute was applied before the first render. */
        this._valueReplayPending = false;
    }

    get tokens() {
        return this._tokens.slice();
    }

    set tokens(val) {
        const list = Array.isArray(val) ? val : [];
        this._tokens = list.map((entry) => this._normalizeItem(entry));
        this._tokensChanged();
    }

    /* The token values joined with commas -- the same form as the `value` attribute. */
    get value() {
        return this._buildValueString();
    }

    set value(val) {
        const text = val !== null && val !== undefined ? String(val) : '';
        this._applyValueString(text);
    }

    get inputValue() {
        const input = this.$('[part="input"]');
        return input != null ? input.value : '';
    }

    set inputValue(val) {
        const input = this.$('[part="input"]');
        if (input != null) {
            input.value = val;
        }
    }

    get dataSource() {
        return this._dataSource;
    }

    set dataSource(val) {
        this._dataSource = val !== undefined ? val : null;
    }

    render() {
        const label = this.getAttribute('aria-label') || t('mj.tagPicker.label');

        return html`
            <div part="container" role="group" aria-label="${label}">
                <span part="token-list"></span>
                <input
                    part="input"
                    id="${this._inputId}"
                    role="combobox"
                    type="text"
                    autocomplete="off"
                    aria-label="${label}"
                    aria-haspopup="listbox"
                    aria-expanded="false"
                    aria-autocomplete="list"
                    aria-controls="${this._listboxId}"
                />
            </div>
            <div part="max-count" id="${this._maxCountId}" hidden>
                <slot name="max-count"><span data-role="max-count-text"></span></slot>
            </div>
            <div part="popup" hidden>
                <div
                    part="listbox"
                    id="${this._listboxId}"
                    role="listbox"
                    aria-label="${t('mj.tagPicker.suggestionsLabel')}"
                    aria-multiselectable="false"
                ></div>
            </div>
            <div id="${this._liveId}" aria-live="polite" aria-atomic="true" class="sr-only"></div>
        `;
    }

    afterRender() {
        const container = this.$('[part="container"]');
        const input = this.$('[part="input"]');
        const tokenList = this.$('[part="token-list"]');
        const listbox = this.$('[part="listbox"]');

        this.listen(container, 'click', (e) => this._onContainerClick(e));
        this.listen(input, 'input', (e) => this._onInput(e));
        this.listen(input, 'keydown', (e) => this._onInputKeydown(e));
        this.listen(this.shadowRoot, 'focusout', (e) => this._onFocusOut(e));

        /* One delegated listener each; the token and option nodes are rebuilt often. */
        this.listen(tokenList, 'click', (e) => this._onTokenListClick(e));
        this.listen(tokenList, 'keydown', (e) => this._onTokenListKeydown(e));
        this.listen(listbox, 'mousedown', (e) => this._onListboxMouseDown(e));

        /* Tokens created from `value` take their label from an option that arrives later. */
        if (typeof MutationObserver === 'function') {
            const observer = new MutationObserver(() => this._relabelTokens());
            observer.observe(this, { childList: true, subtree: true, characterData: true });
            this.onTeardown(() => observer.disconnect());
        }

        /* A fresh render always starts with the popup closed. */
        this._open = false;
        this._activeIndex = -1;

        /* Rebuild the view from the token state (first render and reconnect). */
        this._tokensChanged();
    }

    onDisconnected() {
        this._cancelPendingSuggestions();
        if (this._disposePosition != null) {
            this._disposePosition();
            this._disposePosition = null;
        }
        this._open = false;
    }

    onAttributeChanged(name, oldVal, newVal) {
        if (name === 'value') {
            if (this._rendered === false) {
                this._valueReplayPending = true;
                this._applyValueString(newVal || '');
            } else if (this._valueReplayPending === true) {
                /* The same change was applied before the first render. */
                this._valueReplayPending = false;
            } else {
                this._applyValueString(newVal || '');
            }
        }
        if (name === 'disabled' || name === 'readonly' || name === 'type' ||
            name === 'max-count' || name === 'placeholder') {
            if (name === 'disabled' || name === 'readonly') {
                this._cancelPendingSuggestions();
                this._closePopup();
            }
            this._renderTokens();
            this._updateInputState();
        }
        if (name === 'name') {
            this._syncFormValue();
        }
        if (name === 'required') {
            this._refreshValidity();
        }
        if (name === 'aria-label') {
            const label = newVal || t('mj.tagPicker.label');
            const container = this.$('[part="container"]');
            const input = this.$('[part="input"]');
            if (container != null) {
                container.setAttribute('aria-label', label);
            }
            if (input != null) {
                input.setAttribute('aria-label', label);
            }
        }
    }

    /* Focus goes to the text input, not to the first token's remove button. */
    focus(options) {
        const input = this.$('[part="input"]');
        if (input != null && input.disabled === false) {
            input.focus(options);
        } else {
            super.focus(options);
        }
    }

    _validationAnchor() {
        const input = this.$('[part="input"]');
        return input;
    }

    /* Disabled by its own attribute or by an ancestor <fieldset disabled>. */
    _isDisabled() {
        const disabled = this.hasAttribute('disabled') || this._formDisabled === true;
        return disabled;
    }

    _isInteractive() {
        const blocked = this._isDisabled() || this.hasAttribute('readonly');
        return blocked === false;
    }

    /* An ancestor <fieldset disabled> was switched on or off. */
    onFormDisabled(disabled) {
        this._formDisabled = disabled === true;
        this._cancelPendingSuggestions();
        this._closePopup();
        this._renderTokens();
        this._updateInputState();
    }

    /* An add was attempted at the `max-count` limit: tell listeners and screen readers. */
    _reportMaxCount() {
        const maxCount = this._maxCount();
        this.emit('mj-max-count', { count: maxCount });
        announce(t('mj.tagPicker.maxReached', { count: maxCount }), 'polite');
    }

    _maxCount() {
        const parsed = parseInt(this.getAttribute('max-count') || '0', 10);
        const maxCount = Number.isNaN(parsed) === false && parsed > 0 ? parsed : 0;
        return maxCount;
    }

    _isAtMaxCount() {
        const maxCount = this._maxCount();
        const atMax = maxCount > 0 && this._tokens.length >= maxCount;
        return atMax;
    }

    _inputHasFocus() {
        const input = this.$('[part="input"]');
        const focused = input != null && this.shadowRoot.activeElement === input;
        return focused;
    }

    /* Turn a string or a loosely shaped object into `{ value, label, avatar, meta }`. */
    _normalizeItem(entry) {
        let item = { value: '', label: '', avatar: null, meta: null };

        if (entry !== null && typeof entry === 'object') {
            let value = entry.value;
            if (value === null || value === undefined) {
                value = entry.id;
            }
            let label = entry.label;
            if (label === null || label === undefined) {
                label = entry.name;
            }
            if (value === null || value === undefined) {
                value = label;
            }
            if (label === null || label === undefined) {
                label = value;
            }
            item = {
                value: value !== null && value !== undefined ? String(value) : '',
                label: label !== null && label !== undefined ? String(label) : '',
                avatar: entry.avatar !== null && entry.avatar !== undefined ? String(entry.avatar) : null,
                meta: entry.meta !== null && entry.meta !== undefined ? String(entry.meta) : null,
            };
        } else if (entry !== null && entry !== undefined) {
            const text = String(entry);
            item = { value: text, label: text, avatar: null, meta: null };
        }

        return item;
    }

    /* The <mj-option> children as suggestion items. */
    _readOptions() {
        const items = [];
        this.querySelectorAll('mj-option').forEach((opt) => {
            const label = opt.textContent.trim();
            const value = opt.getAttribute('value') || label;
            const avatar = opt.getAttribute('avatar') || null;
            const meta = opt.getAttribute('meta') || null;
            items.push({ value, label, avatar, meta });
        });
        return items;
    }

    /*
     * Replace the tokens with the comma-separated values in `text`. A value
     * that matches an <mj-option> takes that option's label and avatar; any
     * other value is shown as-is. No event is emitted.
     */
    _applyValueString(text) {
        const parts = text.split(',').map((v) => v.trim()).filter((v) => v.length > 0);
        const options = this._readOptions();

        this._tokens = parts.map((value) => {
            const known = options.find((opt) => opt.value === value);
            const token = known !== undefined
                ? { value: known.value, label: known.label, avatar: known.avatar, meta: null }
                : { value: value, label: value, avatar: null, meta: null };
            return token;
        });
        this._tokensChanged();
    }

    /* Give tokens that still show their raw value the label of a matching <mj-option>. */
    _relabelTokens() {
        const options = this._readOptions();
        let changed = false;

        this._tokens.forEach((token) => {
            if (token.label === token.value) {
                const known = options.find((opt) => opt.value === token.value);
                if (known !== undefined && known.label !== token.label) {
                    token.label = known.label;
                    token.avatar = known.avatar;
                    changed = true;
                }
            }
        });

        if (changed === true) {
            this._renderTokens();
        }
    }

    /* Bring the token list, the input state and the form value in line with `_tokens`. */
    _tokensChanged() {
        this._renderTokens();
        this._updateInputState();
        this._syncFormValue();
    }

    _onContainerClick(e) {
        if (e.target.closest('[part="token-remove"]') != null) {
            return;
        }
        const input = this.$('[part="input"]');
        if (input != null && input.disabled === false) {
            input.focus();
        }
    }

    _onInput(e) {
        const input = e.currentTarget;
        const query = input.value;
        this.emit('mj-input', { inputValue: query });

        clearTimeout(this._debounceTimer);

        const minChars = parseInt(this.getAttribute('min-chars') || '1', 10);
        if (query.length < minChars) {
            this._cancelPendingSuggestions();
            this._closePopup();
            return;
        }

        const debounce = parseInt(this.getAttribute('debounce') || '200', 10);
        this._debounceTimer = setTimeout(() => {
            this._debounceTimer = null;
            if (this._inputHasFocus() === true) {
                this._fetchSuggestions(query);
            }
        }, debounce);
    }

    _onInputKeydown(e) {
        const input = e.currentTarget;
        const key = e.key;
        const freeText = this.hasAttribute('free-text');
        const delimiter = this.getAttribute('delimiter') || ',';

        if (key === 'ArrowDown') {
            e.preventDefault();
            if (!this._open) {
                this._fetchSuggestions(input.value);
            } else {
                this._moveFocus(1);
            }
            return;
        }

        if (key === 'ArrowUp') {
            e.preventDefault();
            this._moveFocus(-1);
            return;
        }

        if (key === 'Home' && this._open) {
            e.preventDefault();
            this._setActiveIndex(0);
            return;
        }

        if (key === 'End' && this._open) {
            e.preventDefault();
            this._setActiveIndex(this._suggestions.length - 1);
            return;
        }

        if (key === 'Enter') {
            e.preventDefault();
            if (this._open && this._activeIndex >= 0) {
                this._selectSuggestion(this._suggestions[this._activeIndex]);
            } else if (freeText && input.value.trim().length > 0) {
                this._addFreeTextToken(input.value.trim());
            } else if (this._isAtMaxCount() === true && input.value.trim().length > 0 && this._isInteractive() === true) {
                /* No suggestions open at the limit: Enter on typed text is the add attempt. */
                this._reportMaxCount();
            }
            return;
        }

        if (key === 'Escape') {
            if (this._open) {
                e.preventDefault();
                this._cancelPendingSuggestions();
                this._closePopup();
                input.value = '';
            }
            return;
        }

        if (key === 'Backspace' && input.value === '') {
            e.preventDefault();
            this._focusLastTokenRemove();
            return;
        }

        if (key === 'ArrowLeft' && input.selectionStart === 0 && input.selectionEnd === 0) {
            this._focusLastTokenRemove();
            return;
        }

        if (freeText && delimiter.length > 0 && key === delimiter) {
            e.preventDefault();
            const text = input.value.trim();
            if (text.length > 0) {
                this._addFreeTextToken(text);
            }
            return;
        }
    }

    _onFocusOut(e) {
        const relatedTarget = e.relatedTarget;
        if (relatedTarget != null && this.shadowRoot.contains(relatedTarget)) {
            return;
        }
        /* Focus left the component: nothing may open the popup afterwards. */
        this._cancelPendingSuggestions();
        this._closePopup();
    }

    /* Stop the debounce timer and any request in flight, and disown its result. */
    _cancelPendingSuggestions() {
        clearTimeout(this._debounceTimer);
        this._debounceTimer = null;
        this._requestSeq = this._requestSeq + 1;
        if (this._abortController != null) {
            this._abortController.abort();
            this._abortController = null;
        }
    }

    _focusLastTokenRemove() {
        const tokenList = this.$('[part="token-list"]');
        if (tokenList == null) {
            return;
        }
        const removeButtons = tokenList.querySelectorAll('[part="token-remove"]:not(:disabled)');
        if (removeButtons.length > 0) {
            removeButtons[removeButtons.length - 1].focus();
        }
    }

    /*
     * Ask the data source for suggestions. Accepts the core DataSource
     * contract (`query(request)` resolving to `{ items }` or an array) and the
     * older `fetch({ query, signal })` shape.
     */
    async _queryDataSource(query, signal) {
        const source = this._dataSource;
        let result = [];

        if (typeof source.query === 'function') {
            result = await source.query({ filter: query, query: query, offset: 0, limit: 50, signal: signal });
        } else if (typeof source.fetch === 'function') {
            result = await source.fetch({ query: query, signal: signal });
        } else if (typeof source === 'function') {
            result = await source({ filter: query, query: query, signal: signal });
        } else {
            throw new TypeError('mj-tag-picker dataSource must provide query(request)');
        }

        let items = [];
        if (Array.isArray(result) === true) {
            items = result;
        } else if (result !== null && result !== undefined && Array.isArray(result.items) === true) {
            items = result.items;
        }
        return items;
    }

    async _querySource(src, query, signal) {
        const url = src + (src.includes('?') ? '&' : '?') + 'q=' + encodeURIComponent(query);
        const response = await fetch(url, { signal: signal });
        if (response.ok === false) {
            throw new Error(`Suggestion request failed with status ${response.status}`);
        }
        const data = await response.json();

        let items = [];
        if (Array.isArray(data) === true) {
            items = data;
        } else if (data !== null && data !== undefined && Array.isArray(data.items) === true) {
            items = data.items;
        }
        return items;
    }

    async _fetchSuggestions(query) {
        if (this._isInteractive() === false || this._isAtMaxCount() === true) {
            return;
        }

        if (this._open === false) {
            const proceed = this.emit('mj-open', {}, { cancelable: true });
            if (proceed === false) {
                return;
            }
        }

        const src = this.getAttribute('src') || '';
        const isAsync = this._dataSource != null || src.length > 0;

        if (isAsync === true) {
            if (this._abortController != null) {
                this._abortController.abort();
            }
            this._abortController = new AbortController();
            this._requestSeq = this._requestSeq + 1;
            const requestSeq = this._requestSeq;
            const signal = this._abortController.signal;

            this._showLoading();

            let items = [];
            let failed = false;
            try {
                if (this._dataSource != null) {
                    items = await this._queryDataSource(query, signal);
                } else {
                    items = await this._querySource(src, query, signal);
                }
            } catch (err) {
                failed = true;
            }

            /* Superseded, cancelled, or focus has left the field: show nothing. */
            if (requestSeq !== this._requestSeq || this._inputHasFocus() === false) {
                return;
            }

            if (failed === true) {
                this._showError();
            } else {
                this._suggestions = items.map((entry) => this._normalizeItem(entry));
                this._showSuggestions(query);
            }
            return;
        }

        /* Sync suggestions from the <mj-option> children. */
        const lowerQuery = query.toLowerCase();
        this._suggestions = this._readOptions().filter((opt) => {
            return opt.label.toLowerCase().includes(lowerQuery);
        });

        this._showSuggestions(query);
    }

    _showLoading() {
        const listbox = this.$('[part="listbox"]');
        if (listbox == null) {
            return;
        }
        listbox.setAttribute('aria-busy', 'true');
        listbox.innerHTML = String(html`<div part="loading"><slot name="loading">${t('mj.tagPicker.loading')}</slot></div>`);
        this._resetActiveOption();
        this._openPopup();
    }

    _showError() {
        const listbox = this.$('[part="listbox"]');
        if (listbox == null) {
            return;
        }
        listbox.removeAttribute('aria-busy');
        listbox.innerHTML = String(html`<div part="no-results">${t('mj.tagPicker.loadError')}</div>`);
        this._suggestions = [];
        this._resetActiveOption();
        this._openPopup();
    }

    _resetActiveOption() {
        this._activeIndex = -1;
        const input = this.$('[part="input"]');
        if (input != null) {
            input.removeAttribute('aria-activedescendant');
        }
    }

    _showSuggestions(query) {
        const listbox = this.$('[part="listbox"]');
        if (listbox == null) {
            return;
        }
        listbox.removeAttribute('aria-busy');

        const duplicateValues = this.hasAttribute('duplicate-values');
        const type = this.getAttribute('type') || 'tag';
        const selectedValues = new Set(this._tokens.map((t) => t.value));

        this._resetActiveOption();

        if (this._suggestions.length === 0) {
            listbox.innerHTML = String(html`<div part="no-results"><slot name="no-results">${t('mj.tagPicker.noResults')}</slot></div>`);
            announce(t('mj.tagPicker.noResults'), 'polite');
            this._openPopup();
            return;
        }

        const items = this._suggestions.map((s, idx) => {
            const alreadySelected = !duplicateValues && selectedValues.has(s.value);
            const optId = `${this._listboxId}-opt-${idx}`;
            const highlighted = this._highlightMatch(s.label, query);
            const avatarHtml = this._buildAvatar(s, type, 'option-avatar');
            const metaHtml = s.meta != null ? html`<span part="option-meta">${s.meta}</span>` : '';
            const alreadyClass = alreadySelected ? 'already-selected' : '';

            return html`
                <div
                    part="option"
                    id="${optId}"
                    role="option"
                    data-index="${idx}"
                    aria-selected="${alreadySelected ? 'true' : 'false'}"
                    aria-disabled="${alreadySelected ? 'true' : 'false'}"
                    class="${alreadyClass}"
                >
                    ${avatarHtml}
                    <span part="option-label">${highlighted}</span>
                    ${metaHtml}
                </div>
            `;
        });

        listbox.innerHTML = String(html`${items}`);
        this._openPopup();
    }

    _onListboxMouseDown(e) {
        /* Keep focus in the input so the popup is not dismissed by its own click. */
        e.preventDefault();

        const optEl = e.target.closest('[part="option"]');
        if (optEl == null || optEl.classList.contains('already-selected')) {
            return;
        }
        const idx = parseInt(optEl.dataset.index, 10);
        if (!isNaN(idx) && idx >= 0 && idx < this._suggestions.length) {
            this._selectSuggestion(this._suggestions[idx]);
        }
    }

    /* The avatar markup for a token or an option in person mode. */
    _buildAvatar(item, type, partName) {
        if (type !== 'person') {
            return '';
        }
        if (item.avatar != null && item.avatar !== '') {
            return html`<img part="${partName}" src="${safeUrl(item.avatar, '')}" alt="" aria-hidden="true">`;
        }
        const initials = this._getInitials(item.label);
        return html`<span part="${partName}" class="initials" aria-hidden="true">${initials}</span>`;
    }

    _getInitials(label) {
        const text = String(label).trim();
        const words = text.split(/\s+/).filter((word) => word.length > 0);
        if (words.length >= 2) {
            return (words[0][0] + words[1][0]).toUpperCase();
        }
        return text.slice(0, 2).toUpperCase();
    }

    /* The label as escaped markup with the first match of `query` wrapped in <mark>. */
    _highlightMatch(label, query) {
        const normalLabel = String(label).normalize('NFC');
        const normalQuery = String(query).normalize('NFC');
        let highlighted = html`${normalLabel}`;

        if (normalQuery.length > 0) {
            const idx = normalLabel.toLowerCase().indexOf(normalQuery.toLowerCase());
            if (idx >= 0) {
                const before = normalLabel.slice(0, idx);
                const match = normalLabel.slice(idx, idx + normalQuery.length);
                const after = normalLabel.slice(idx + normalQuery.length);
                highlighted = html`${before}<mark>${match}</mark>${after}`;
            }
        }

        return highlighted;
    }

    _openPopup() {
        if (this._open) {
            return;
        }
        const popup = this.$('[part="popup"]');
        const container = this.$('[part="container"]');
        if (popup == null || container == null) {
            return;
        }
        popup.hidden = false;
        popup.style.minWidth = `${Math.round(container.getBoundingClientRect().width)}px`;
        this._open = true;

        const input = this.$('[part="input"]');
        if (input != null) {
            input.setAttribute('aria-expanded', 'true');
        }

        if (this._disposePosition != null) {
            this._disposePosition();
        }
        this._disposePosition = autoPosition(popup, container, { placement: 'bottom-start' });
    }

    _closePopup() {
        if (!this._open) {
            return;
        }
        const popup = this.$('[part="popup"]');
        if (popup != null) {
            popup.hidden = true;
        }
        this._open = false;
        this._activeIndex = -1;

        const input = this.$('[part="input"]');
        if (input != null) {
            input.setAttribute('aria-expanded', 'false');
            input.removeAttribute('aria-activedescendant');
        }

        if (this._disposePosition != null) {
            this._disposePosition();
            this._disposePosition = null;
        }

        this.emit('mj-close', {});
    }

    _moveFocus(delta) {
        if (!this._open || this._suggestions.length === 0) {
            return;
        }
        const newIndex = Math.max(0, Math.min(this._suggestions.length - 1, this._activeIndex + delta));
        this._setActiveIndex(newIndex);
    }

    _setActiveIndex(idx) {
        this._activeIndex = idx;
        const listbox = this.$('[part="listbox"]');
        const input = this.$('[part="input"]');
        if (listbox == null) {
            return;
        }

        const options = listbox.querySelectorAll('[part="option"]');
        options.forEach((opt, i) => {
            if (i === idx) {
                opt.classList.add('active');
                opt.scrollIntoView({ block: 'nearest' });
                if (input != null) {
                    input.setAttribute('aria-activedescendant', opt.id);
                }
            } else {
                opt.classList.remove('active');
            }
        });
    }

    _selectSuggestion(suggestion) {
        const token = {
            value: suggestion.value,
            label: suggestion.label,
            avatar: suggestion.avatar || null,
        };
        this._addToken(token);
    }

    _addFreeTextToken(text) {
        const token = { value: text, label: text, avatar: null };
        this._addToken(token);
    }

    /*
     * Add one token on behalf of the user. Returns true when it was added;
     * false when the limit is reached, the value is a duplicate, or a
     * `mj-token-add` listener cancelled it (the typed text is then kept).
     */
    _addToken(token) {
        if (this._isInteractive() === false) {
            return false;
        }

        const maxCount = this._maxCount();
        if (this._isAtMaxCount() === true) {
            this._reportMaxCount();
            return false;
        }

        const duplicateValues = this.hasAttribute('duplicate-values');
        if (!duplicateValues) {
            const exists = this._tokens.some((t) => t.value === token.value);
            if (exists) {
                return false;
            }
        }

        const proceed = this.emit('mj-token-add', { token }, { cancelable: true });
        if (proceed === false) {
            return false;
        }

        const input = this.$('[part="input"]');
        if (input != null) {
            input.value = '';
        }

        this._tokens.push(token);
        this._cancelPendingSuggestions();
        this._closePopup();
        this._tokensChanged();

        announce(t('mj.tagPicker.tokenAdded', { count: this._tokens.length, label: token.label }), 'polite');
        if (this._isAtMaxCount() === true) {
            announce(t('mj.tagPicker.maxReached', { count: maxCount }), 'polite');
        }
        this.emit('mj-change', { tokens: this.tokens, values: this._tokens.map((t) => t.value) });
        return true;
    }

    _removeToken(idx) {
        if (this._isInteractive() === false) {
            return;
        }
        if (idx < 0 || idx >= this._tokens.length) {
            return;
        }
        const token = this._tokens[idx];
        this._tokens.splice(idx, 1);
        this._tokensChanged();

        announce(t('mj.tagPicker.tokenRemoved', { count: this._tokens.length, label: token.label }), 'polite');
        this.emit('mj-token-remove', { token });
        this.emit('mj-change', { tokens: this.tokens, values: this._tokens.map((t) => t.value) });

        // Restore focus to input or adjacent token
        const tokenList = this.$('[part="token-list"]');
        const removeButtons = tokenList != null ? tokenList.querySelectorAll('[part="token-remove"]') : [];
        if (removeButtons.length > 0) {
            const focusIdx = Math.min(idx, removeButtons.length - 1);
            removeButtons[focusIdx].focus();
        } else {
            const input = this.$('[part="input"]');
            if (input != null) {
                input.focus();
            }
        }
    }

    _renderTokens() {
        const tokenList = this.$('[part="token-list"]');
        if (tokenList == null) {
            return;
        }
        const readonly = this.hasAttribute('readonly');
        const disabled = this._isDisabled();
        const type = this.getAttribute('type') || 'tag';

        const items = this._tokens.map((token, idx) => {
            const avatarHtml = this._buildAvatar(token, type, 'token-avatar');
            const removeHtml = readonly ? '' : html`
                <button
                    part="token-remove"
                    type="button"
                    aria-label="${t('mj.tagPicker.removeToken', { label: token.label })}"
                    data-token-idx="${idx}"
                >×</button>
            `;
            return html`
                <span part="token" data-value="${token.value}">
                    ${avatarHtml}
                    <span part="token-label">${token.label}</span>
                    ${removeHtml}
                </span>
            `;
        });

        tokenList.innerHTML = String(html`${items}`);

        /* A disabled picker keeps its tokens but they cannot be removed. */
        tokenList.querySelectorAll('[part="token-remove"]').forEach((btn) => {
            btn.disabled = disabled;
        });
    }

    _onTokenListClick(e) {
        const btn = e.target.closest('[part="token-remove"]');
        if (btn == null) {
            return;
        }
        e.stopPropagation();
        const tokenIdx = parseInt(btn.dataset.tokenIdx, 10);
        this._removeToken(tokenIdx);
    }

    _onTokenListKeydown(e) {
        const btn = e.target.closest('[part="token-remove"]');
        if (btn == null) {
            return;
        }
        const btnIdx = parseInt(btn.dataset.tokenIdx, 10);
        const tokenList = this.$('[part="token-list"]');
        const buttons = tokenList.querySelectorAll('[part="token-remove"]');

        if (e.key === 'Backspace' || e.key === 'Delete') {
            e.preventDefault();
            this._removeToken(btnIdx);
        } else if (e.key === 'ArrowRight') {
            if (btnIdx < buttons.length - 1) {
                buttons[btnIdx + 1].focus();
            } else {
                const input = this.$('[part="input"]');
                if (input != null && input.disabled === false) {
                    input.focus();
                }
            }
        } else if (e.key === 'ArrowLeft') {
            if (btnIdx > 0) {
                buttons[btnIdx - 1].focus();
            }
        }
    }

    _updateInputState() {
        const input = this.$('[part="input"]');
        if (input == null) {
            return;
        }
        const disabled = this._isDisabled();
        const readonly = this.hasAttribute('readonly');
        const maxCount = this._maxCount();
        const atMax = this._isAtMaxCount();

        /*
         * At the limit the input stays focusable (Backspace still reaches the
         * tokens) but no longer opens suggestions; an add attempted there
         * fires mj-max-count. The hint describes the input meanwhile.
         */
        input.disabled = disabled;
        input.readOnly = readonly;
        if (atMax === true) {
            input.setAttribute('aria-describedby', this._maxCountId);
        } else {
            input.removeAttribute('aria-describedby');
        }

        /* The placeholder is a hint for an empty field only. */
        const placeholder = this.getAttribute('placeholder') || '';
        input.placeholder = this._tokens.length === 0 ? placeholder : '';

        const container = this.$('[part="container"]');
        if (container != null) {
            if (disabled) {
                container.setAttribute('aria-disabled', 'true');
            } else {
                container.removeAttribute('aria-disabled');
            }
            if (readonly) {
                container.setAttribute('aria-readonly', 'true');
            } else {
                container.removeAttribute('aria-readonly');
            }
        }

        const hint = this.$('[part="max-count"]');
        const hintText = this.$('[data-role="max-count-text"]');
        if (hint != null) {
            hint.hidden = atMax === false;
        }
        if (hintText != null) {
            hintText.textContent = t('mj.tagPicker.maxReached', { count: maxCount });
        }
    }

    _buildValueString() {
        return this._tokens.map((t) => t.value).join(',');
    }

    /*
     * Submit one `name=value` entry per token. `_value` holds the joined
     * string so the mixin's `required` check sees an empty picker as empty.
     */
    _syncFormValue() {
        const joined = this._buildValueString();
        const name = this.getAttribute('name') || '';

        this._value = joined;
        if (this._internals != null) {
            const fd = new FormData();
            if (name.length > 0) {
                this._tokens.forEach((t) => fd.append(name, t.value));
            }
            this._internals.setFormValue(fd, joined);
        }
        this._refreshValidity();
    }

    /* Reset restores the tokens named by the `value` attribute. */
    formResetCallback() {
        this._cancelPendingSuggestions();
        this._closePopup();
        const input = this.$('[part="input"]');
        if (input != null) {
            input.value = '';
        }
        this._applyValueString(this.getAttribute('value') || '');
    }

    formStateRestoreCallback(state) {
        if (typeof state === 'string') {
            this._applyValueString(state);
        }
    }
}
