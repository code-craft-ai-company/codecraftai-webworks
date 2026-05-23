import { MjElement, nextId } from '../core/mjelement.js';
import { FormControlMixin } from '../core/forminternals.js';
import { autoPosition } from '../core/overlay.js';
import { announce } from '../core/announcer.js';
import { DataSource } from '../core/collection.js';

export class MjTagPicker extends FormControlMixin(MjElement) {
    static tagName = 'mj-tag-picker';

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
            flex-wrap: wrap;
            align-items: center;
            gap: var(--mj-tag-picker-token-gap, var(--mj-space-1));
            min-height: var(--mj-tag-picker-min-height, var(--mj-size-control-md));
            padding: var(--mj-space-1) var(--mj-space-2);
            border: var(--mj-border-width-sm) solid var(--mj-color-border-default);
            border-radius: var(--mj-tag-picker-border-radius, var(--mj-radius-md));
            background: var(--mj-color-surface-default);
            cursor: text;
            transition: border-color var(--mj-motion-duration-fast) var(--mj-motion-easing-default);
        }
        :host([aria-invalid="true"]) [part="container"] {
            border-color: var(--mj-color-border-danger);
        }
        [part="container"]:focus-within {
            border-color: var(--mj-color-border-focus);
            outline: var(--mj-border-width-md) solid var(--mj-color-focus-ring);
            outline-offset: 2px;
        }
        [part="token-list"] {
            display: contents;
        }
        [part="token"] {
            display: inline-flex;
            align-items: center;
            gap: var(--mj-space-1);
            padding: 0 var(--mj-space-2);
            height: 1.625rem;
            background: var(--mj-tag-picker-token-bg, var(--mj-color-surface-subtle));
            border: var(--mj-border-width-sm) solid var(--mj-color-border-subtle);
            border-radius: var(--mj-tag-picker-token-radius, var(--mj-radius-full));
            font-size: var(--mj-font-size-sm);
            white-space: nowrap;
        }
        [part="token-avatar"] {
            width: var(--mj-tag-picker-avatar-size, 1.25rem);
            height: var(--mj-tag-picker-avatar-size, 1.25rem);
            border-radius: 50%;
            object-fit: cover;
            flex-shrink: 0;
        }
        [part="token-avatar"].initials {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--mj-color-brand-subtle);
            color: var(--mj-color-brand-emphasis);
            font-size: 0.625rem;
            font-weight: var(--mj-font-weight-semibold);
        }
        [part="token-remove"] {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1rem;
            height: 1rem;
            min-width: 44px;
            min-height: 44px;
            padding: 0;
            margin: 0 -0.375rem;
            background: none;
            border: none;
            cursor: pointer;
            color: var(--mj-color-text-subtle);
            border-radius: var(--mj-radius-sm);
            position: relative;
        }
        [part="token-remove"]:hover {
            color: var(--mj-color-text-default);
            background: var(--mj-color-surface-hover);
        }
        [part="token-remove"]:focus-visible {
            outline: var(--mj-border-width-md) solid var(--mj-color-focus-ring);
            outline-offset: 1px;
        }
        [part="input"] {
            flex: 1;
            min-width: 8rem;
            height: 1.625rem;
            border: none;
            background: transparent;
            font-family: inherit;
            font-size: inherit;
            color: var(--mj-color-text-default);
            outline: none;
        }
        [part="input"]::placeholder {
            color: var(--mj-color-text-placeholder);
        }
        [part="input"]:disabled {
            pointer-events: none;
        }
        [part="popup"] {
            position: fixed;
            z-index: var(--mj-z-index-dropdown);
            background: var(--mj-color-surface-overlay);
            border: var(--mj-border-width-sm) solid var(--mj-color-border-default);
            border-radius: var(--mj-radius-md);
            box-shadow: var(--mj-shadow-md);
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
            background: var(--mj-color-surface-hover);
        }
        [part="option"].active {
            background: var(--mj-color-surface-selected);
        }
        [part="option"].already-selected {
            opacity: 0.5;
            cursor: default;
        }
        [part="option-avatar"] {
            width: var(--mj-tag-picker-avatar-size, 1.25rem);
            height: var(--mj-tag-picker-avatar-size, 1.25rem);
            border-radius: 50%;
            object-fit: cover;
            flex-shrink: 0;
        }
        [part="option-avatar"].initials {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--mj-color-brand-subtle);
            color: var(--mj-color-brand-emphasis);
            font-size: 0.625rem;
            font-weight: var(--mj-font-weight-semibold);
        }
        [part="option-label"] {
            flex: 1;
        }
        [part="option-meta"] {
            font-size: var(--mj-font-size-sm);
            color: var(--mj-color-text-subtle);
        }
        [part="option-label"] mark {
            background: var(--mj-color-highlight);
            color: inherit;
            border-radius: 2px;
        }
        [part="no-results"],
        [part="loading"],
        [part="max-count"] {
            padding: var(--mj-space-3);
            text-align: center;
            color: var(--mj-color-text-subtle);
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
        'duplicate-values', 'delimiter'];

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
        this._abortController = null;
    }

    get tokens() {
        return this._tokens.slice();
    }

    set tokens(val) {
        this._tokens = Array.isArray(val) ? val.slice() : [];
        this._syncFormValue();
        this._renderTokens();
        this._updateInputState();
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
        this._dataSource = val;
    }

    render() {
        const placeholder = this.getAttribute('placeholder') || '';
        const type = this.getAttribute('type') || 'tag';

        return `
            <div part="container" role="group" aria-label="${this.getAttribute('aria-label') || 'Tag picker'}">
                <span part="token-list" id="${nextId('mj-tp-tl')}"></span>
                <input
                    part="input"
                    id="${this._inputId}"
                    role="combobox"
                    type="text"
                    autocomplete="off"
                    placeholder="${placeholder}"
                    aria-haspopup="listbox"
                    aria-expanded="false"
                    aria-autocomplete="list"
                    aria-controls="${this._listboxId}"
                />
            </div>
            <div part="popup" hidden>
                <div
                    part="listbox"
                    id="${this._listboxId}"
                    role="listbox"
                    aria-label="Suggestions"
                    aria-multiselectable="false"
                ></div>
            </div>
            <div id="${this._liveId}" aria-live="polite" aria-atomic="true" class="sr-only"></div>
        `;
    }

    afterRender() {
        const container = this.$('[part="container"]');
        const input = this.$('[part="input"]');
        const popup = this.$('[part="popup"]');

        this.listen(container, 'click', (e) => this._onContainerClick(e));
        this.listen(input, 'input', (e) => this._onInput(e));
        this.listen(input, 'keydown', (e) => this._onInputKeydown(e));
        this.listen(input, 'blur', (e) => this._onInputBlur(e));
        this.listen(this.shadowRoot, 'focusout', (e) => this._onFocusOut(e));

        const initialValue = this.getAttribute('value') || '';
        if (initialValue.length > 0) {
            const parts = initialValue.split(',').map((v) => v.trim()).filter((v) => v.length > 0);
            this._tokens = parts.map((v) => ({ value: v, label: v }));
            this._renderTokens();
            this._syncFormValue();
        }

        this._updateInputState();
    }

    onAttributeChanged(name, oldVal, newVal) {
        if (name === 'value' && newVal !== this._buildValueString()) {
            const parts = (newVal || '').split(',').map((v) => v.trim()).filter((v) => v.length > 0);
            this._tokens = parts.map((v) => ({ value: v, label: v }));
            this._renderTokens();
            this._syncFormValue();
        }
        if (name === 'disabled' || name === 'readonly') {
            this._updateInputState();
        }
        if (name === 'placeholder') {
            const input = this.$('[part="input"]');
            if (input != null && newVal != null) {
                input.setAttribute('placeholder', newVal);
            }
        }
    }

    _onContainerClick(e) {
        if (e.target.closest('[part="token-remove"]') != null) {
            return;
        }
        const input = this.$('[part="input"]');
        if (input != null) {
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
            this._closePopup();
            return;
        }

        const debounce = parseInt(this.getAttribute('debounce') || '200', 10);
        this._debounceTimer = setTimeout(() => {
            this._fetchSuggestions(query);
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
            }
            return;
        }

        if (key === 'Escape') {
            if (this._open) {
                e.preventDefault();
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

    _onInputBlur() {
        // handled by focusout on shadow root
    }

    _onFocusOut(e) {
        const relatedTarget = e.relatedTarget;
        if (relatedTarget != null && this.shadowRoot.contains(relatedTarget)) {
            return;
        }
        this._closePopup();
    }

    _focusLastTokenRemove() {
        if (this._tokens.length === 0) {
            return;
        }
        const tokenList = this.$('[part="token-list"]');
        if (tokenList == null) {
            return;
        }
        const removeButtons = tokenList.querySelectorAll('[part="token-remove"]');
        if (removeButtons.length > 0) {
            removeButtons[removeButtons.length - 1].focus();
        }
    }

    async _fetchSuggestions(query) {
        const maxCount = parseInt(this.getAttribute('max-count') || '0', 10);
        if (maxCount > 0 && this._tokens.length >= maxCount) {
            return;
        }

        const openEvent = this.emit('mj-open', {}, { cancelable: true });
        if (openEvent.defaultPrevented) {
            return;
        }

        const src = this.getAttribute('src') || '';

        if (this._dataSource != null) {
            this._showLoading();
            try {
                if (this._abortController != null) {
                    this._abortController.abort();
                }
                this._abortController = new AbortController();
                const results = await this._dataSource.fetch({ query: query, signal: this._abortController.signal });
                this._suggestions = Array.isArray(results) ? results : [];
                this._showSuggestions(query);
            } catch (err) {
                if (err.name !== 'AbortError') {
                    this._showError();
                }
            }
            return;
        }

        if (src.length > 0) {
            this._showLoading();
            try {
                if (this._abortController != null) {
                    this._abortController.abort();
                }
                this._abortController = new AbortController();
                const url = src + (src.includes('?') ? '&' : '?') + 'q=' + encodeURIComponent(query);
                const response = await fetch(url, { signal: this._abortController.signal });
                const data = await response.json();
                this._suggestions = Array.isArray(data) ? data : (data.items || []);
                this._showSuggestions(query);
            } catch (err) {
                if (err.name !== 'AbortError') {
                    this._showError();
                }
            }
            return;
        }

        // Sync suggestions from slotted mj-option elements
        const slottedOptions = this.querySelectorAll('mj-option');
        const lowerQuery = query.toLowerCase();
        this._suggestions = [];

        slottedOptions.forEach((opt) => {
            const label = opt.textContent.trim();
            const value = opt.getAttribute('value') || label;
            if (label.toLowerCase().includes(lowerQuery)) {
                const avatar = opt.getAttribute('avatar') || null;
                const meta = opt.getAttribute('meta') || null;
                this._suggestions.push({ value, label, avatar, meta });
            }
        });

        this._showSuggestions(query);
    }

    _showLoading() {
        const listbox = this.$('[part="listbox"]');
        if (listbox == null) {
            return;
        }
        listbox.setAttribute('aria-busy', 'true');
        listbox.innerHTML = `<div part="loading">Loading…</div>`;
        this._openPopup();
    }

    _showError() {
        const listbox = this.$('[part="listbox"]');
        if (listbox == null) {
            return;
        }
        listbox.removeAttribute('aria-busy');
        listbox.innerHTML = `<div part="no-results">Failed to load suggestions.</div>`;
        this._openPopup();
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

        if (this._suggestions.length === 0) {
            listbox.innerHTML = `<div part="no-results">No results found.</div>`;
            announce('No results found.', 'polite');
            this._openPopup();
            return;
        }

        const lowerQuery = query.toLowerCase();
        const items = this._suggestions.map((s, idx) => {
            const alreadySelected = !duplicateValues && selectedValues.has(s.value);
            const optId = nextId('mj-tp-opt');
            const highlighted = this._highlightMatch(s.label, lowerQuery);
            const avatarHtml = this._buildOptionAvatar(s, type);
            const metaHtml = s.meta != null ? `<span part="option-meta">${s.meta}</span>` : '';
            const alreadyClass = alreadySelected ? ' already-selected' : '';

            return `
                <div
                    part="option"
                    id="${optId}"
                    role="option"
                    data-value="${s.value}"
                    data-index="${idx}"
                    aria-selected="${alreadySelected ? 'true' : 'false'}"
                    class="${alreadyClass}"
                >
                    ${avatarHtml}
                    <span part="option-label">${highlighted}</span>
                    ${metaHtml}
                </div>
            `;
        });

        listbox.innerHTML = items.join('');
        this._activeIndex = -1;

        const input = this.$('[part="input"]');
        if (input != null) {
            input.removeAttribute('aria-activedescendant');
        }

        this.listen(listbox, 'mousedown', (e) => {
            const optEl = e.target.closest('[part="option"]');
            if (optEl == null) {
                return;
            }
            if (optEl.classList.contains('already-selected')) {
                return;
            }
            e.preventDefault();
            const idx = parseInt(optEl.dataset.index, 10);
            if (!isNaN(idx) && idx >= 0 && idx < this._suggestions.length) {
                this._selectSuggestion(this._suggestions[idx]);
            }
        });

        this._openPopup();
    }

    _buildOptionAvatar(suggestion, type) {
        if (type !== 'person') {
            return '';
        }
        if (suggestion.avatar != null) {
            return `<img part="option-avatar" src="${suggestion.avatar}" alt="" aria-hidden="true">`;
        }
        const initials = this._getInitials(suggestion.label);
        return `<span part="option-avatar initials" aria-hidden="true">${initials}</span>`;
    }

    _buildTokenAvatar(token, type) {
        if (type !== 'person') {
            return '';
        }
        if (token.avatar != null) {
            return `<img part="token-avatar" src="${token.avatar}" alt="" aria-hidden="true">`;
        }
        const initials = this._getInitials(token.label);
        return `<span part="token-avatar initials" aria-hidden="true">${initials}</span>`;
    }

    _getInitials(label) {
        const words = label.trim().split(/\s+/);
        if (words.length >= 2) {
            return (words[0][0] + words[1][0]).toUpperCase();
        }
        return label.slice(0, 2).toUpperCase();
    }

    _highlightMatch(label, query) {
        if (query.length === 0) {
            return label;
        }
        const normalLabel = label.normalize('NFC');
        const normalQuery = query.normalize('NFC');
        const idx = normalLabel.toLowerCase().indexOf(normalQuery.toLowerCase());
        if (idx < 0) {
            return label;
        }
        const before = label.slice(0, idx);
        const match = label.slice(idx, idx + query.length);
        const after = label.slice(idx + query.length);
        return `${before}<mark>${match}</mark>${after}`;
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
        const maxCount = parseInt(this.getAttribute('max-count') || '0', 10);
        if (maxCount > 0 && this._tokens.length >= maxCount) {
            this.emit('mj-max-count', { count: maxCount });
            announce(`Maximum ${maxCount} tags reached.`, 'polite');
            return;
        }

        const duplicateValues = this.hasAttribute('duplicate-values');
        if (!duplicateValues) {
            const exists = this._tokens.some((t) => t.value === suggestion.value);
            if (exists) {
                return;
            }
        }

        const token = {
            value: suggestion.value,
            label: suggestion.label,
            avatar: suggestion.avatar || null,
        };

        const addEvent = this.emit('mj-token-add', { token }, { cancelable: true });
        if (addEvent.defaultPrevented) {
            return;
        }

        this._tokens.push(token);
        this._renderTokens();
        this._syncFormValue();

        const input = this.$('[part="input"]');
        if (input != null) {
            input.value = '';
        }

        this._closePopup();
        announce(`${token.label} added. ${this._tokens.length} tag${this._tokens.length !== 1 ? 's' : ''} selected.`, 'polite');
        this.emit('mj-change', { tokens: this.tokens, values: this._tokens.map((t) => t.value) });
    }

    _addFreeTextToken(text) {
        const maxCount = parseInt(this.getAttribute('max-count') || '0', 10);
        if (maxCount > 0 && this._tokens.length >= maxCount) {
            this.emit('mj-max-count', { count: maxCount });
            announce(`Maximum ${maxCount} tags reached.`, 'polite');
            return;
        }

        const duplicateValues = this.hasAttribute('duplicate-values');
        if (!duplicateValues) {
            const exists = this._tokens.some((t) => t.value === text);
            if (exists) {
                return;
            }
        }

        const token = { value: text, label: text, avatar: null };
        const addEvent = this.emit('mj-token-add', { token }, { cancelable: true });
        if (addEvent.defaultPrevented) {
            return;
        }

        this._tokens.push(token);
        this._renderTokens();
        this._syncFormValue();

        const input = this.$('[part="input"]');
        if (input != null) {
            input.value = '';
        }

        announce(`${token.label} added. ${this._tokens.length} tag${this._tokens.length !== 1 ? 's' : ''} selected.`, 'polite');
        this.emit('mj-change', { tokens: this.tokens, values: this._tokens.map((t) => t.value) });
    }

    _removeToken(idx) {
        if (idx < 0 || idx >= this._tokens.length) {
            return;
        }
        const token = this._tokens[idx];
        this._tokens.splice(idx, 1);
        this._renderTokens();
        this._syncFormValue();

        announce(`${token.label} removed. ${this._tokens.length} tag${this._tokens.length !== 1 ? 's' : ''} selected.`, 'polite');
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
        const type = this.getAttribute('type') || 'tag';

        const html = this._tokens.map((token, idx) => {
            const avatarHtml = this._buildTokenAvatar(token, type);
            const removeHtml = readonly ? '' : `
                <button
                    part="token-remove"
                    type="button"
                    aria-label="Remove ${token.label}"
                    data-token-idx="${idx}"
                    tabindex="0"
                >×</button>
            `;
            return `
                <span part="token" data-value="${token.value}">
                    ${avatarHtml}
                    <span part="token-label">${token.label}</span>
                    ${removeHtml}
                </span>
            `;
        });

        tokenList.innerHTML = html.join('');

        // Wire remove buttons
        tokenList.querySelectorAll('[part="token-remove"]').forEach((btn) => {
            this.listen(btn, 'click', (e) => {
                e.stopPropagation();
                const tokenIdx = parseInt(btn.dataset.tokenIdx, 10);
                this._removeToken(tokenIdx);
            });
            this.listen(btn, 'keydown', (e) => {
                const btnIdx = parseInt(btn.dataset.tokenIdx, 10);
                if (e.key === 'Backspace' || e.key === 'Delete') {
                    e.preventDefault();
                    this._removeToken(btnIdx);
                } else if (e.key === 'ArrowRight') {
                    const tokenList2 = this.$('[part="token-list"]');
                    const buttons = tokenList2 != null ? tokenList2.querySelectorAll('[part="token-remove"]') : [];
                    if (btnIdx < buttons.length - 1) {
                        buttons[btnIdx + 1].focus();
                    } else {
                        const input = this.$('[part="input"]');
                        if (input != null) {
                            input.focus();
                        }
                    }
                } else if (e.key === 'ArrowLeft') {
                    const tokenList2 = this.$('[part="token-list"]');
                    const buttons = tokenList2 != null ? tokenList2.querySelectorAll('[part="token-remove"]') : [];
                    if (btnIdx > 0) {
                        buttons[btnIdx - 1].focus();
                    }
                }
            });
        });
    }

    _updateInputState() {
        const input = this.$('[part="input"]');
        if (input == null) {
            return;
        }
        const disabled = this.hasAttribute('disabled');
        const readonly = this.hasAttribute('readonly');
        const maxCount = parseInt(this.getAttribute('max-count') || '0', 10);
        const atMax = maxCount > 0 && this._tokens.length >= maxCount;

        if (disabled || readonly || atMax) {
            input.setAttribute('disabled', '');
        } else {
            input.removeAttribute('disabled');
        }

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
    }

    _buildValueString() {
        return this._tokens.map((t) => t.value).join(',');
    }

    _syncFormValue() {
        const fd = new FormData();
        const name = this.getAttribute('name') || '';
        if (name.length > 0) {
            this._tokens.forEach((t) => fd.append(name, t.value));
        }
        this._setFormValue(fd);
        this.reflectBoolean('value', this._buildValueString());
        this._customValidity(this._computeValidity());
    }

    _computeValidity() {
        const required = this.hasAttribute('required');
        if (required && this._tokens.length === 0) {
            return 'Please select at least one tag.';
        }
        return '';
    }

    formResetCallback() {
        const initialValue = this.getAttribute('value') || '';
        const parts = initialValue.split(',').map((v) => v.trim()).filter((v) => v.length > 0);
        this._tokens = parts.map((v) => ({ value: v, label: v }));
        this._renderTokens();
        this._syncFormValue();
        this._updateInputState();
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        if (this._disposePosition != null) {
            this._disposePosition();
            this._disposePosition = null;
        }
        if (this._abortController != null) {
            this._abortController.abort();
            this._abortController = null;
        }
        clearTimeout(this._debounceTimer);
    }
}
