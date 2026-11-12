import { MjElement, nextId } from '../core/mjelement.js';
import { FormControlMixin } from '../core/forminternals.js';
import { announce } from '../core/announcer.js';
import { html } from '../core/html.js';
import { t } from '../core/intl.js';

/*
 * mj-tree-selector -- a collapsible tree with single, multi or tri-state
 * checkbox selection.
 *
 * State lives in fields and the rows are rebuilt from them (`_renderTree`):
 *   _nodes        the tree data (`nodes` property or <mj-tree-item> children)
 *   _selectedIds  ids of the selected nodes. In checkbox mode only nodes
 *                 without children are stored; a parent is checked, mixed or
 *                 unchecked according to its descendants and is part of the
 *                 value exactly when it is fully checked.
 *   _expandedIds  ids of the expanded branches
 *   _focusedId    the row that holds the single tab stop (roving tabindex)
 *
 * A node is `{ id, label, value?, icon?, badge?, disabled?, children?,
 * hasChildren? }`. A node without `children` (undefined or null) is a leaf
 * unless `hasChildren` is true; `children: []` is a known-empty branch.
 *
 * The `value` attribute is the INITIAL selection (comma-separated node ids or
 * values; in single mode only the first one listed is kept); user changes
 * are not reflected back to it. `expanded` sets the expanded branches
 * explicitly; without it `default-expanded` ("root", "all", "none" or a
 * comma-separated id list) applies until the user toggles a branch. A lazy
 * branch (`hasChildren` without `children`) that is expanded and shown loads
 * its children from `dataSource.getChildren(id)`, however it was expanded.
 */
export class MjTreeSelector extends FormControlMixin(MjElement) {
    static tagName = 'mj-tree-selector';

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
        [part="tree"] {
            padding: var(--mj-space-1);
            outline: none;
        }
        [part="tree"]:focus-visible {
            outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
            outline-offset: -2px;
        }
        [part="tree-item"] {
            display: block;
        }
        .tree-item-row {
            display: flex;
            align-items: center;
            height: var(--mj-tree-item-height, 2rem);
            padding-inline-start: calc(var(--level, 0) * var(--mj-tree-item-indent, 1.25rem));
            padding-inline-end: var(--mj-space-2);
            gap: var(--mj-tree-item-gap, var(--mj-space-2));
            border-inline-start: 3px solid transparent;
            border-radius: var(--mj-radius-sm);
            cursor: pointer;
            user-select: none;
            position: relative;
        }
        .tree-item-row:hover {
            background: var(--mj-bg-subtle);
        }
        .tree-item-row:focus {
            outline: none;
        }
        .tree-item-row:focus-visible {
            outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
            outline-offset: -2px;
        }
        .tree-item-row[aria-selected="true"] {
            background: var(--mj-tree-selected-bg, var(--mj-bg-muted));
            border-inline-start-color: var(--mj-accent);
            font-weight: var(--mj-font-weight-medium);
        }
        .tree-item-row[aria-disabled="true"] {
            opacity: 0.45;
            cursor: not-allowed;
        }
        [part="item-toggle"] {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: var(--mj-tree-toggle-size, 1.25rem);
            height: var(--mj-tree-toggle-size, 1.25rem);
            flex-shrink: 0;
            cursor: pointer;
            color: var(--mj-text-muted);
            transition: transform var(--mj-motion-fast) var(--mj-motion-ease);
        }
        :host(:dir(rtl)) [part="item-toggle"] {
            transform: scaleX(-1);
        }
        [part="item-toggle"].expanded,
        :host(:dir(rtl)) [part="item-toggle"].expanded {
            transform: rotate(90deg);
        }
        [part="item-toggle"].leaf {
            visibility: hidden;
        }
        [part="item-checkbox"] {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: var(--mj-tree-checkbox-size, 1rem);
            height: var(--mj-tree-checkbox-size, 1rem);
            flex-shrink: 0;
            border: 1px solid var(--mj-border-strong);
            border-radius: var(--mj-radius-sm);
            background: var(--mj-surface);
            font-size: 0.625rem;
            font-weight: var(--mj-font-weight-bold);
            line-height: 1;
        }
        [part="item-checkbox"].checked,
        [part="item-checkbox"].indeterminate {
            background: var(--mj-accent);
            border-color: var(--mj-accent);
            color: var(--mj-text-on-accent);
        }
        [part="item-icon"] {
            width: 1rem;
            height: 1rem;
            flex-shrink: 0;
            color: var(--mj-text-muted);
        }
        [part="item-label"] {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        [part="item-badge"] {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 1.25rem;
            height: 1.25rem;
            padding: 0 var(--mj-space-1);
            background: var(--mj-bg-muted);
            border-radius: var(--mj-radius-pill);
            font-size: var(--mj-font-size-xs);
            color: var(--mj-text-muted);
        }
        [part="item-children"] {
            display: block;
        }
        [part="item-children"][hidden] {
            display: none;
        }
        [part="item-loading"] {
            display: flex;
            align-items: center;
            padding: var(--mj-space-2) var(--mj-space-3);
            padding-inline-start: calc(var(--level, 0) * var(--mj-tree-item-indent, 1.25rem) + var(--mj-space-3));
            color: var(--mj-text-muted);
            font-size: var(--mj-font-size-sm);
        }
        [part="empty"] {
            padding: var(--mj-space-4);
            text-align: center;
            color: var(--mj-text-muted);
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

    static watched = ['name', 'value', 'selection', 'disabled', 'required',
        'single-expand', 'expanded', 'default-expanded', 'aria-label'];

    constructor() {
        super();
        this._initFormControl();

        this._nodes = [];
        this._selectedIds = new Set();
        this._expandedIds = new Set();
        this._loadingIds = new Set();
        this._dataSource = null;
        this._typeaheadBuffer = '';
        this._typeaheadTimer = null;
        this._treeId = nextId('mj-tree');
        this._liveId = nextId('mj-tree-live');
        this._rowIdPrefix = nextId('mj-tn-row');
        this._rowSeq = 0;
        this._focusedId = null;

        /* The row a Shift+click range starts from. */
        this._anchorId = null;

        /* The selection mode the current selection was made in. */
        this._selectionMode = 'single';

        /* True once the user expanded or collapsed a branch; defaults then stop applying. */
        this._userToggled = false;

        /* True when the nodes were read from <mj-tree-item> children. */
        this._nodesFromLightDom = false;

        /* Stable generated ids for <mj-tree-item> elements without `node-id`. */
        this._lightDomIds = new WeakMap();

        /* True when the `value` attribute was applied before the first render. */
        this._valueReplayPending = false;

        this._formDisabled = false;
    }

    get nodes() {
        return this._nodes;
    }

    set nodes(val) {
        this._nodes = Array.isArray(val) ? val : [];
        this._nodesFromLightDom = false;
        this._nodesChanged();
    }

    /*
     * The selected node objects. In checkbox mode these are all fully checked
     * nodes: the checked leaves and every parent whose descendants are all
     * checked.
     */
    get selectedNodes() {
        const allNodes = this._flattenNodes(this._nodes);
        const selection = this._selection();

        let selected = [];
        if (selection === 'checkbox') {
            selected = allNodes.filter((n) => this._getCheckState(n) === 'true');
        } else if (selection !== 'none') {
            selected = allNodes.filter((n) => this._selectedIds.has(this._idOf(n)));
        }
        return selected;
    }

    get expandedNodeIds() {
        return new Set(this._expandedIds);
    }

    get dataSource() {
        return this._dataSource;
    }

    set dataSource(val) {
        this._dataSource = val !== undefined ? val : null;
        /* Lazy branches already expanded by the attributes can load now. */
        this._loadExpandedLazyBranches();
    }

    /* The selected node values joined with commas -- the same form as the `value` attribute. */
    get value() {
        return this._selectedValues().join(',');
    }

    set value(val) {
        const text = val !== null && val !== undefined ? String(val) : '';
        this._applyValueString(text);
    }

    render() {
        const label = this.getAttribute('aria-label') || t('mj.treeSelector.label');

        return html`
            <div
                part="tree"
                id="${this._treeId}"
                role="tree"
                tabindex="0"
                aria-label="${label}"
            ></div>
            <div id="${this._liveId}" aria-live="polite" aria-atomic="true" class="sr-only"></div>
        `;
    }

    afterRender() {
        const tree = this.$('[part="tree"]');

        this.listen(tree, 'keydown', (e) => this._onTreeKeydown(e));
        this.listen(tree, 'click', (e) => this._onTreeClick(e));

        /* <mj-tree-item> children added or changed after the first connect. */
        if (typeof MutationObserver === 'function') {
            const observer = new MutationObserver(() => this._onLightDomChanged());
            observer.observe(this, { childList: true, subtree: true, characterData: true, attributes: true,
                attributeFilter: ['label', 'value', 'icon', 'badge', 'disabled', 'has-children', 'node-id'] });
            this.onTeardown(() => observer.disconnect());
        }
        this.onTeardown(() => clearTimeout(this._typeaheadTimer));

        if (this._nodes.length === 0 || this._nodesFromLightDom === true) {
            this._readLightDom();
        }

        /*
         * On the first render this applies the default expansion; on a
         * reconnect the user's expanded branches and selection are kept and
         * only the rows are rebuilt.
         */
        this._nodesChanged();
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
        if (name === 'selection') {
            const mode = this._selection();
            if (mode !== this._selectionMode) {
                this._selectionMode = mode;
                if (this._rendered === true) {
                    /* A selection made in one mode does not carry over to another. */
                    this._selectedIds.clear();
                } else {
                    this._normalizeSelection();
                }
                this._renderTree();
                this._syncFormValue();
            }
        }
        if (name === 'expanded' || name === 'default-expanded') {
            if (name === 'expanded' || this._userToggled === false) {
                this._applyExpansionAttributes();
                this._renderTree();
                this._loadExpandedLazyBranches();
            }
        }
        if (name === 'disabled') {
            this._renderTree();
        }
        if (name === 'name') {
            this._syncFormValue();
        }
        if (name === 'required') {
            this._refreshValidity();
        }
        if (name === 'aria-label') {
            const tree = this.$('[part="tree"]');
            if (tree != null) {
                tree.setAttribute('aria-label', newVal || t('mj.treeSelector.label'));
            }
        }
    }

    onFormDisabled(disabled) {
        this._formDisabled = disabled === true;
        this._renderTree();
    }

    /* Focus goes to the row that holds the tab stop. */
    focus(options) {
        const tree = this.$('[part="tree"]');
        const target = tree != null ? tree.querySelector('.tree-item-row[tabindex="0"]') : null;
        if (target != null) {
            target.focus(options);
        } else {
            super.focus(options);
        }
    }

    _validationAnchor() {
        const tree = this.$('[part="tree"]');
        let anchor = null;
        if (tree != null) {
            anchor = tree.querySelector('.tree-item-row[tabindex="0"]');
            if (anchor == null) {
                anchor = tree;
            }
        }
        return anchor;
    }

    /* `required` does not apply to a tree that offers no selection. */
    _refreshValidity() {
        if (this._internals == null) {
            return;
        }
        if (this._selection() === 'none') {
            this._internals.setValidity({});
        } else {
            super._refreshValidity();
        }
    }

    _selection() {
        const raw = this.getAttribute('selection') || 'single';
        const known = raw === 'single' || raw === 'multi' || raw === 'checkbox' || raw === 'none';
        return known === true ? raw : 'single';
    }

    _isDisabled() {
        const disabled = this.hasAttribute('disabled') || this._formDisabled === true;
        return disabled;
    }

    /* Node ids are compared as strings: they travel through data attributes. */
    _idOf(node) {
        return String(node.id);
    }

    _hasChildList(node) {
        const has = Array.isArray(node.children) === true && node.children.length > 0;
        return has;
    }

    /* A leaf has no `children` array and does not announce lazy children. */
    _isLeaf(node) {
        const leaf = Array.isArray(node.children) === false && node.hasChildren !== true;
        return leaf;
    }

    _splitList(text) {
        const parts = String(text || '').split(',').map((v) => v.trim()).filter((v) => v.length > 0);
        return parts;
    }

    /* ----- light DOM ----- */

    _readLightDom() {
        const items = this.querySelectorAll(':scope > mj-tree-item');
        if (items.length > 0 || this._nodesFromLightDom === true) {
            this._nodes = this._parseTreeItems(items);
            this._nodesFromLightDom = true;
        }
    }

    _onLightDomChanged() {
        if (this._nodesFromLightDom === true || this._nodes.length === 0) {
            this._readLightDom();
            this._nodesChanged();
        }
    }

    /* The text an <mj-tree-item> carries itself, without its nested items. */
    _ownText(item) {
        let text = '';
        item.childNodes.forEach((child) => {
            if (child.nodeType === Node.TEXT_NODE) {
                text += child.textContent;
            }
        });
        return text.trim();
    }

    _parseTreeItems(items) {
        const nodes = [];
        items.forEach((item) => {
            let id = item.getAttribute('node-id');
            if (id === null || id === '') {
                id = this._lightDomIds.get(item);
                if (id === undefined) {
                    id = nextId('mj-tn');
                    this._lightDomIds.set(item, id);
                }
            }
            const label = item.getAttribute('label') || this._ownText(item);
            const value = item.getAttribute('value') || id;
            const icon = item.getAttribute('icon') || null;
            const badge = item.getAttribute('badge') || null;
            const disabled = item.hasAttribute('disabled');
            const hasChildren = item.hasAttribute('has-children');
            const childItems = item.querySelectorAll(':scope > mj-tree-item');
            const children = childItems.length > 0 ? this._parseTreeItems(childItems) : undefined;

            nodes.push({ id, label, value, icon, badge, disabled, hasChildren, children });
        });
        return nodes;
    }

    /* ----- state changes ----- */

    /* The tree data changed: re-resolve selection and expansion, then repaint. */
    _nodesChanged() {
        if (this._userToggled === false) {
            this._applyExpansionAttributes();
        }
        this._normalizeSelection();
        this._renderTree();
        this._syncFormValue();
        this._loadExpandedLazyBranches();
    }

    /*
     * Set the expanded branches from the attributes: `expanded` when present,
     * otherwise `default-expanded` ("root" when absent).
     */
    _applyExpansionAttributes() {
        const expandedAttr = this.getAttribute('expanded');
        const next = new Set();

        if (expandedAttr !== null) {
            this._splitList(expandedAttr).forEach((id) => next.add(id));
        } else {
            const mode = this.getAttribute('default-expanded') || 'root';
            if (mode === 'root') {
                this._nodes.forEach((n) => {
                    if (this._isLeaf(n) === false && n.hasChildren !== true) {
                        next.add(this._idOf(n));
                    }
                });
            } else if (mode === 'all') {
                this._flattenNodes(this._nodes).forEach((n) => {
                    if (this._isLeaf(n) === false && n.hasChildren !== true) {
                        next.add(this._idOf(n));
                    }
                });
            } else if (mode !== 'none') {
                this._splitList(mode).forEach((id) => next.add(id));
            }
        }

        this._expandedIds = next;
    }

    /*
     * Select the nodes named in `text` (comma-separated ids or values). Names
     * that match no node yet are held and take effect when the node appears.
     * No event is emitted.
     */
    _applyValueString(text) {
        this._selectedIds = new Set(this._splitList(text));
        this._normalizeSelection();
        this._renderTree();
        this._syncFormValue();
    }

    /*
     * Bring `_selectedIds` into its canonical form: entries given as a node
     * value become that node's id, and in checkbox mode a selected parent is
     * replaced by its descendants without children.
     */
    _normalizeSelection() {
        const allNodes = this._flattenNodes(this._nodes);
        const byId = new Map();
        allNodes.forEach((n) => byId.set(this._idOf(n), n));

        const next = new Set();
        this._selectedIds.forEach((entry) => {
            let node = byId.get(entry);
            if (node === undefined) {
                node = allNodes.find((n) => n.value !== null && n.value !== undefined && String(n.value) === entry);
            }

            if (node === undefined) {
                next.add(entry);
            } else if (this._selection() === 'checkbox' && this._hasChildList(node) === true) {
                this._leafNodes(node.children).forEach((leaf) => next.add(this._idOf(leaf)));
            } else {
                next.add(this._idOf(node));
            }
        });

        /* Single mode holds one node at most: the first one listed wins. */
        if (this._selection() === 'single' && next.size > 1) {
            const first = next.values().next().value;
            next.clear();
            next.add(first);
        }

        this._selectedIds = next;
    }

    /* The descendants of `nodes` (inclusive) that have no child list. */
    _leafNodes(nodes) {
        const leaves = this._flattenNodes(nodes).filter((n) => this._hasChildList(n) === false);
        return leaves;
    }

    _selectedValues() {
        const values = this.selectedNodes.map((n) => {
            const value = n.value !== null && n.value !== undefined && n.value !== '' ? n.value : n.id;
            return String(value);
        });
        return values;
    }

    /* ----- rendering ----- */

    _renderTree() {
        const treeEl = this.$('[part="tree"]');
        if (treeEl == null) {
            return;
        }

        /* Rebuilding the rows destroys the focused one; remember to restore it. */
        const active = this.shadowRoot.activeElement;
        const hadFocus = active !== null && treeEl.contains(active) === true;

        if (this._isDisabled() === true) {
            treeEl.setAttribute('aria-disabled', 'true');
        } else {
            treeEl.removeAttribute('aria-disabled');
        }
        if (this._selection() === 'multi' || this._selection() === 'checkbox') {
            treeEl.setAttribute('aria-multiselectable', 'true');
        } else {
            treeEl.removeAttribute('aria-multiselectable');
        }

        if (this._nodes.length === 0) {
            treeEl.innerHTML = String(html`<div part="empty"><slot name="empty">${t('mj.treeSelector.empty')}</slot></div>`);
            this._focusedId = null;
            this._updateTabindex();
            return;
        }

        this._rowSeq = 0;
        treeEl.innerHTML = String(this._renderNodes(this._nodes, 1, new Set()));

        this._ensureFocusedRow();
        this._updateTabindex();

        if (hadFocus === true) {
            const row = this._rowFor(this._focusedId);
            if (row != null) {
                row.focus();
            }
        }
    }

    _renderNodes(nodes, level, ancestors) {
        const parts = [];
        nodes.forEach((node, idx) => {
            /* A node that is its own ancestor would recurse forever. */
            if (ancestors.has(this._idOf(node)) === true) {
                console.error(`mj-tree-selector: node "${this._idOf(node)}" is its own ancestor; skipped`);
                return;
            }
            parts.push(this._renderNode(node, level, idx, nodes.length, ancestors));
        });
        return html`${parts}`;
    }

    _renderNode(node, level, posInSet, setSize, ancestors) {
        const selection = this._selection();
        const id = this._idOf(node);
        const isLeaf = this._isLeaf(node);
        const isExpanded = this._expandedIds.has(id);
        const isSelected = this._selectedIds.has(id);
        const isLoading = this._loadingIds.has(id);
        const label = node.label !== null && node.label !== undefined ? String(node.label) : '';

        this._rowSeq = this._rowSeq + 1;
        const rowId = `${this._rowIdPrefix}-${this._rowSeq}`;

        const toggleClass = isLeaf ? 'leaf' : (isExpanded ? 'expanded' : '');
        const toggleEl = html`
            <span
                part="item-toggle"
                class="${toggleClass}"
                aria-hidden="true"
                data-action="toggle"
            >›</span>
        `;

        /* State attributes that are present only in some modes or states. */
        const stateAttrs = [];
        let checkboxHtml = '';
        if (selection === 'checkbox') {
            const checkState = this._getCheckState(node);
            const checkClass = checkState === 'true' ? 'checked' : (checkState === 'mixed' ? 'indeterminate' : '');
            const checkGlyph = checkState === 'true' ? '✓' : (checkState === 'mixed' ? '–' : '');
            checkboxHtml = html`
                <span
                    part="item-checkbox"
                    class="${checkClass}"
                    aria-hidden="true"
                >${checkGlyph}</span>
            `;
            stateAttrs.push(html` aria-checked="${checkState}"`);
        } else if (selection === 'single' || selection === 'multi') {
            stateAttrs.push(html` aria-selected="${isSelected ? 'true' : 'false'}"`);
        }
        if (!isLeaf) {
            stateAttrs.push(html` aria-expanded="${isExpanded ? 'true' : 'false'}"`);
        }
        if (isLoading) {
            stateAttrs.push(html` aria-busy="true"`);
        }
        if (node.disabled === true) {
            stateAttrs.push(html` aria-disabled="true"`);
        }

        const iconHtml = node.icon != null ? html`<span part="item-icon" aria-hidden="true">${node.icon}</span>` : '';
        const badgeHtml = node.badge != null ? html`<span part="item-badge">${node.badge}</span>` : '';

        const rowHtml = html`
            <div
                class="tree-item-row"
                role="treeitem"
                id="${rowId}"
                tabindex="-1"
                data-node-id="${id}"
                style="--level: ${level - 1}"
                aria-level="${level}"
                aria-setsize="${setSize}"
                aria-posinset="${posInSet + 1}"
                ${stateAttrs}
            >
                ${toggleEl}
                ${checkboxHtml}
                ${iconHtml}
                <span part="item-label">${label}</span>
                ${badgeHtml}
            </div>
        `;

        let childrenHtml = '';
        if (!isLeaf) {
            let childContent = '';
            if (isLoading) {
                childContent = html`<div part="item-loading" style="--level: ${level}"><slot name="loading">${t('mj.treeSelector.loading')}</slot></div>`;
            } else if (isExpanded && this._hasChildList(node) === true) {
                const nextAncestors = new Set(ancestors);
                nextAncestors.add(id);
                childContent = this._renderNodes(node.children, level + 1, nextAncestors);
            }
            const hiddenAttr = isExpanded ? '' : html` hidden`;
            childrenHtml = html`
                <div
                    part="item-children"
                    role="group"
                    ${hiddenAttr}
                >${childContent}</div>
            `;
        }

        return html`<div part="tree-item">${rowHtml}${childrenHtml}</div>`;
    }

    /* Find the rendered row of a node id, or null. */
    _rowFor(nodeId) {
        const treeEl = this.$('[part="tree"]');
        if (treeEl == null || nodeId === null || nodeId === undefined) {
            return null;
        }
        const rows = Array.from(treeEl.querySelectorAll('.tree-item-row'));
        const row = rows.find((r) => r.dataset.nodeId === String(nodeId));
        return row !== undefined ? row : null;
    }

    /*
     * Keep the roving tab stop on a row that exists and is visible. When the
     * focused node is no longer rendered (its parent was collapsed, the data
     * changed) the stop moves to its nearest rendered ancestor, else to the
     * first row.
     */
    _ensureFocusedRow() {
        const visible = this._getVisibleRows();
        const isVisible = (nodeId) => visible.some((r) => r.dataset.nodeId === nodeId);

        if (this._focusedId !== null && isVisible(this._focusedId) === true) {
            return;
        }

        let replacement = null;
        if (this._focusedId !== null) {
            let parent = this._findParentNode(this._focusedId, this._nodes);
            while (parent !== null && replacement === null) {
                const parentId = this._idOf(parent);
                if (isVisible(parentId) === true) {
                    replacement = parentId;
                } else {
                    parent = this._findParentNode(parentId, this._nodes);
                }
            }
        }
        if (replacement === null && visible.length > 0) {
            replacement = visible[0].dataset.nodeId;
        }

        this._focusedId = replacement;
    }

    _getCheckState(node) {
        const id = this._idOf(node);
        if (this._hasChildList(node) === false) {
            return this._selectedIds.has(id) ? 'true' : 'false';
        }

        const leaves = this._leafNodes(node.children);
        const enabled = leaves.filter((n) => n.disabled !== true);
        const counted = enabled.length > 0 ? enabled : leaves;
        const selectedCount = counted.filter((n) => this._selectedIds.has(this._idOf(n))).length;

        if (selectedCount === 0) {
            return 'false';
        }
        if (selectedCount === counted.length) {
            return 'true';
        }
        return 'mixed';
    }

    _flattenNodes(nodes) {
        const result = [];
        const seen = new Set();
        const walk = (nodeList) => {
            nodeList.forEach((n) => {
                if (n === null || typeof n !== 'object' || seen.has(n) === true) {
                    return;
                }
                seen.add(n);
                result.push(n);
                if (this._hasChildList(n) === true) {
                    walk(n.children);
                }
            });
        };
        walk(nodes);
        return result;
    }

    _findNode(id) {
        const wanted = String(id);
        const found = this._flattenNodes(this._nodes).find((n) => this._idOf(n) === wanted);
        return found !== undefined ? found : null;
    }

    _findParentNode(nodeId) {
        const wanted = String(nodeId);
        const found = this._flattenNodes(this._nodes).find((n) => {
            return this._hasChildList(n) === true && n.children.some((c) => this._idOf(c) === wanted);
        });
        return found !== undefined ? found : null;
    }

    /* ----- interaction ----- */

    _onTreeClick(e) {
        if (this._isDisabled() === true) {
            return;
        }
        const row = e.target.closest('.tree-item-row');
        if (row == null) {
            return;
        }
        const nodeId = row.dataset.nodeId;
        const node = this._findNode(nodeId);
        if (node == null) {
            return;
        }

        /* The clicked row takes the tab stop, whatever else the click does. */
        this._focusedId = nodeId;
        this._updateTabindex();
        row.focus();

        const toggle = e.target.closest('[data-action="toggle"]');
        if (toggle != null) {
            this._toggleExpand(node);
            return;
        }

        const selection = this._selection();
        if (selection === 'none') {
            this._toggleExpand(node);
            return;
        }

        if (node.disabled === true) {
            return;
        }

        if (selection === 'checkbox') {
            this._toggleCheckbox(node);
        } else if (selection === 'single') {
            this._selectSingle(nodeId);
        } else if (selection === 'multi') {
            if (e.ctrlKey || e.metaKey) {
                this._toggleMultiSelect(nodeId);
            } else if (e.shiftKey) {
                this._selectRange(nodeId);
            } else {
                this._selectSingle(nodeId);
            }
        }
    }

    _onTreeKeydown(e) {
        if (this._isDisabled() === true) {
            return;
        }
        const rows = this._getVisibleRows();
        const currentIdx = rows.findIndex((r) => r.dataset.nodeId === this._focusedId);

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (currentIdx < rows.length - 1) {
                this._setFocusedRow(rows[currentIdx + 1]);
            }
            return;
        }

        if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (currentIdx > 0) {
                this._setFocusedRow(rows[currentIdx - 1]);
            }
            return;
        }

        if (e.key === 'Home') {
            e.preventDefault();
            if (rows.length > 0) {
                this._setFocusedRow(rows[0]);
            }
            return;
        }

        if (e.key === 'End') {
            e.preventDefault();
            if (rows.length > 0) {
                this._setFocusedRow(rows[rows.length - 1]);
            }
            return;
        }

        if (e.key === 'ArrowRight') {
            e.preventDefault();
            const nodeId = this._focusedId;
            const node = nodeId !== null ? this._findNode(nodeId) : null;
            if (node == null || this._isLeaf(node) === true) {
                return;
            }
            if (!this._expandedIds.has(nodeId)) {
                this._toggleExpand(node);
            } else {
                // Move to first child
                const nextRow = rows[currentIdx + 1];
                const currentRow = rows[currentIdx];
                if (nextRow != null && currentRow != null &&
                    Number(nextRow.getAttribute('aria-level')) > Number(currentRow.getAttribute('aria-level'))) {
                    this._setFocusedRow(nextRow);
                }
            }
            return;
        }

        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            const nodeId = this._focusedId;
            const node = nodeId !== null ? this._findNode(nodeId) : null;
            if (node == null) {
                return;
            }
            if (this._isLeaf(node) === false && this._expandedIds.has(nodeId)) {
                this._toggleExpand(node);
            } else {
                // Move to parent
                const parentNode = this._findParentNode(nodeId);
                const parentRow = parentNode !== null ? this._rowFor(this._idOf(parentNode)) : null;
                if (parentRow != null) {
                    this._setFocusedRow(parentRow);
                }
            }
            return;
        }

        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            const nodeId = this._focusedId;
            const node = nodeId !== null ? this._findNode(nodeId) : null;
            if (node == null) {
                return;
            }
            const selection = this._selection();
            if (selection === 'none') {
                this._toggleExpand(node);
            } else if (node.disabled === true) {
                return;
            } else if (selection === 'checkbox') {
                this._toggleCheckbox(node);
            } else if (selection === 'single') {
                this._selectSingle(nodeId);
            } else if (selection === 'multi') {
                this._toggleMultiSelect(nodeId);
            }
            return;
        }

        if (e.key === '*') {
            e.preventDefault();
            this._expandAllSiblings();
            return;
        }

        // Type-ahead
        if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
            clearTimeout(this._typeaheadTimer);
            this._typeaheadBuffer += e.key.toLowerCase();
            this._typeaheadTimer = setTimeout(() => {
                this._typeaheadBuffer = '';
            }, 500);

            /* A repeated first letter cycles; a longer prefix may match the current row. */
            const startIdx = this._typeaheadBuffer.length > 1 ? Math.max(currentIdx, 0) : currentIdx + 1;
            const searchOrder = [...rows.slice(startIdx), ...rows.slice(0, startIdx)];
            const match = searchOrder.find((r) => {
                const node = this._findNode(r.dataset.nodeId);
                if (node == null) {
                    return false;
                }
                return String(node.label).toLowerCase().startsWith(this._typeaheadBuffer);
            });
            if (match != null) {
                this._setFocusedRow(match);
            }
            return;
        }
    }

    _getVisibleRows() {
        const tree = this.$('[part="tree"]');
        if (tree == null) {
            return [];
        }
        // Only rows that are not inside a hidden children container
        const allRows = Array.from(tree.querySelectorAll('.tree-item-row'));
        return allRows.filter((row) => {
            let parent = row.parentElement;
            while (parent != null && parent !== tree) {
                if (parent.getAttribute('part') === 'item-children' && parent.hidden) {
                    return false;
                }
                parent = parent.parentElement;
            }
            return true;
        });
    }

    _setFocusedRow(row) {
        this._focusedId = row.dataset.nodeId;
        this._updateTabindex();
        row.focus();
    }

    /*
     * Roving tabindex: exactly one tab stop. It is the focused row; the tree
     * container takes it only when there is no row at all, and a disabled
     * tree has none.
     */
    _updateTabindex() {
        const treeEl = this.$('[part="tree"]');
        if (treeEl == null) {
            return;
        }
        const disabled = this._isDisabled();
        const rows = treeEl.querySelectorAll('.tree-item-row');
        let hasStop = false;

        rows.forEach((row) => {
            const isStop = disabled === false && row.dataset.nodeId === this._focusedId;
            row.tabIndex = isStop === true ? 0 : -1;
            if (isStop === true) {
                hasStop = true;
            }
        });

        treeEl.tabIndex = hasStop === true || disabled === true ? -1 : 0;
    }

    async _toggleExpand(node) {
        const id = this._idOf(node);
        if (this._isLeaf(node) === true) {
            return;
        }

        if (this._expandedIds.has(id)) {
            // Collapse
            this._userToggled = true;
            this._expandedIds.delete(id);
            this._renderTree();
            announce(t('mj.treeSelector.collapsed', { label: node.label }), 'polite');
            this.emit('mj-collapse', { nodeId: node.id, node });
            return;
        }

        // Expand
        const proceed = this.emit('mj-expand', { nodeId: node.id, node }, { cancelable: true });
        if (proceed === false) {
            return;
        }

        this._userToggled = true;
        this._expandedIds.add(id);

        // Single-expand mode
        if (this.hasAttribute('single-expand')) {
            const parent = this._findParentNode(id);
            const siblings = parent != null ? parent.children : this._nodes;
            siblings.forEach((sibling) => {
                if (this._idOf(sibling) !== id) {
                    this._expandedIds.delete(this._idOf(sibling));
                }
            });
        }

        // Async children
        const needsLoad = node.hasChildren === true && this._hasChildList(node) === false &&
            this._loadingIds.has(id) === false &&
            this._dataSource != null && typeof this._dataSource.getChildren === 'function';
        if (needsLoad === true) {
            await this._loadChildren(node);
            return;
        }

        this._renderTree();
        announce(t('mj.treeSelector.expanded', { label: node.label }), 'polite');
        /* Expanded lazy branches inside it are shown now. */
        this._loadExpandedLazyBranches();
    }

    /* Load a lazy branch's children from the data source and show them. */
    async _loadChildren(node) {
        const id = this._idOf(node);
        this._loadingIds.add(id);
        this._renderTree();
        announce(t('mj.treeSelector.loadingChildren', { label: node.label }), 'polite');
        this.emit('mj-node-load-start', { nodeId: node.id });

        try {
            const children = await this._dataSource.getChildren(node.id);
            node.children = Array.isArray(children) ? children : [];
            this._loadingIds.delete(id);
            /* A parent checked while loading passes its state on to the children. */
            this._normalizeSelection();
            this._renderTree();
            this._syncFormValue();
            announce(t('mj.treeSelector.loaded', { count: node.children.length }), 'polite');
            this.emit('mj-node-load-end', { nodeId: node.id, children: node.children });
        } catch (err) {
            node.children = [];
            this._loadingIds.delete(id);
            this._renderTree();
            this.emit('mj-node-error', { nodeId: node.id, error: err });
        }

        /* Expanded lazy branches among the new children load in turn. */
        this._loadExpandedLazyBranches();
    }

    /*
     * Load the children of every shown branch that is expanded but has never
     * had a child list (`hasChildren` without `children`): one expanded by
     * `expanded` / `default-expanded`, or inside a branch that was just
     * expanded or loaded. A branch under a collapsed parent waits until it is
     * shown; a branch whose load returned no children (or failed) has
     * `children: []` and is not loaded again here.
     */
    _loadExpandedLazyBranches() {
        const source = this._dataSource;
        const treeEl = this.$('[part="tree"]');
        if (treeEl == null || source == null || typeof source.getChildren !== 'function') {
            return;
        }

        const pending = [];
        const visit = (nodes) => {
            nodes.forEach((node) => {
                const id = this._idOf(node);
                if (this._expandedIds.has(id) === false) {
                    return;
                }
                const neverLoaded = node.hasChildren === true && Array.isArray(node.children) === false;
                if (neverLoaded === true) {
                    if (this._loadingIds.has(id) === false) {
                        pending.push(node);
                    }
                } else if (this._hasChildList(node) === true) {
                    visit(node.children);
                }
            });
        };
        visit(this._nodes);

        pending.forEach((node) => {
            this._loadChildren(node);
        });
    }

    _selectionChanged() {
        this._renderTree();
        this._syncFormValue();
        this._emitChange();
    }

    _selectSingle(nodeId) {
        const prevSelected = new Set(this._selectedIds);
        this._selectedIds.clear();
        this._selectedIds.add(nodeId);
        this._anchorId = nodeId;

        if (!this._setsEqual(prevSelected, this._selectedIds)) {
            this._selectionChanged();
        }
    }

    _toggleMultiSelect(nodeId) {
        if (this._selectedIds.has(nodeId)) {
            this._selectedIds.delete(nodeId);
        } else {
            this._selectedIds.add(nodeId);
        }
        this._anchorId = nodeId;
        this._selectionChanged();
    }

    _selectRange(endNodeId) {
        const rows = this._getVisibleRows();
        let startIdx = rows.findIndex((r) => r.dataset.nodeId === this._anchorId);
        if (startIdx < 0) {
            startIdx = rows.findIndex((r) => this._selectedIds.has(r.dataset.nodeId));
        }
        const endIdx = rows.findIndex((r) => r.dataset.nodeId === endNodeId);

        if (startIdx < 0 || endIdx < 0) {
            this._toggleMultiSelect(endNodeId);
            return;
        }

        const lo = Math.min(startIdx, endIdx);
        const hi = Math.max(startIdx, endIdx);
        rows.slice(lo, hi + 1).forEach((r) => {
            if (r.getAttribute('aria-disabled') !== 'true') {
                this._selectedIds.add(r.dataset.nodeId);
            }
        });

        this._selectionChanged();
    }

    _toggleCheckbox(node) {
        const currentState = this._getCheckState(node);

        if (currentState === 'true') {
            // Uncheck self and all children
            this._setCheckRecursive(node, false);
        } else {
            // Check self and all children
            this._setCheckRecursive(node, true);
        }

        this._selectionChanged();
    }

    /*
     * Check or uncheck a node. Only nodes without children are stored; a
     * parent's state always follows from its descendants, so it can never
     * stay in the value after one of them is unchecked.
     */
    _setCheckRecursive(node, checked) {
        if (node.disabled === true) {
            return;
        }
        if (this._hasChildList(node) === true) {
            node.children.forEach((child) => this._setCheckRecursive(child, checked));
        } else if (checked) {
            this._selectedIds.add(this._idOf(node));
        } else {
            this._selectedIds.delete(this._idOf(node));
        }
    }

    _expandAllSiblings() {
        const nodeId = this._focusedId;
        if (nodeId == null) {
            return;
        }
        const parentNode = this._findParentNode(nodeId);
        const siblings = parentNode != null ? parentNode.children : this._nodes;
        this._userToggled = true;
        siblings.forEach((sibling) => {
            /* Lazy branches load on an explicit expand only. */
            if (Array.isArray(sibling.children) === true) {
                this._expandedIds.add(this._idOf(sibling));
            }
        });
        this._renderTree();
    }

    _setsEqual(a, b) {
        if (a.size !== b.size) {
            return false;
        }
        for (const val of a) {
            if (!b.has(val)) {
                return false;
            }
        }
        return true;
    }

    _emitChange() {
        const selectedNodes = this.selectedNodes;
        const values = this._selectedValues();
        this.emit('mj-change', { values, selectedNodes });
    }

    /*
     * Submit one `name=value` entry per selected node. `_value` holds the
     * joined string so the mixin's `required` check sees an empty selection
     * as empty.
     */
    _syncFormValue() {
        const values = this._selectedValues();
        const joined = values.join(',');
        const name = this.getAttribute('name') || '';

        this._value = joined;
        if (this._internals != null) {
            const fd = new FormData();
            if (name.length > 0) {
                values.forEach((value) => fd.append(name, value));
            }
            this._internals.setFormValue(fd, joined);
        }
        this._refreshValidity();
    }

    /* Reset restores the `value` attribute's selection and the default expansion. */
    formResetCallback() {
        this._userToggled = false;
        this._applyExpansionAttributes();
        this._anchorId = null;
        this._applyValueString(this.getAttribute('value') || '');
    }

    formStateRestoreCallback(state) {
        if (typeof state === 'string') {
            this._applyValueString(state);
        }
    }
}
