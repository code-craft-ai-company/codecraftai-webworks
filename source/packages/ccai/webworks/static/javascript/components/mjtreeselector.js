import { MjElement, nextId } from '../core/mjelement.js';
import { FormControlMixin } from '../core/forminternals.js';
import { announce } from '../core/announcer.js';

export class MjTreeSelector extends FormControlMixin(MjElement) {
    static tagName = 'mj-tree-selector';

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
        [part="tree"] {
            padding: var(--mj-space-1);
            outline: none;
        }
        [part="tree-item"] {
            display: block;
        }
        .tree-item-row {
            display: flex;
            align-items: center;
            height: var(--mj-tree-item-height, 2rem);
            padding-inline-start: calc(var(--level, 0) * var(--mj-tree-item-indent, 1.25rem));
            gap: var(--mj-tree-item-gap, var(--mj-space-2));
            border-radius: var(--mj-radius-sm);
            cursor: pointer;
            user-select: none;
            position: relative;
        }
        .tree-item-row:hover {
            background: var(--mj-color-surface-hover);
        }
        .tree-item-row:focus-visible,
        .tree-item-row.focused {
            outline: var(--mj-border-width-md) solid var(--mj-color-focus-ring);
            outline-offset: -2px;
        }
        .tree-item-row[aria-selected="true"],
        .tree-item-row[aria-checked="true"] {
            background: var(--mj-tree-selected-bg, var(--mj-color-selected-subtle));
        }
        [part="item-toggle"] {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: var(--mj-tree-toggle-size, 1.25rem);
            height: var(--mj-tree-toggle-size, 1.25rem);
            flex-shrink: 0;
            background: none;
            border: none;
            padding: 0;
            cursor: pointer;
            color: var(--mj-color-text-subtle);
            transition: transform var(--mj-motion-duration-fast) var(--mj-motion-easing-default);
        }
        [part="item-toggle"]:focus-visible {
            outline: var(--mj-border-width-md) solid var(--mj-color-focus-ring);
            border-radius: var(--mj-radius-sm);
        }
        [part="item-toggle"].expanded {
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
            border: var(--mj-border-width-sm) solid var(--mj-color-border-strong);
            border-radius: var(--mj-radius-sm);
            background: var(--mj-color-surface-default);
            font-size: 0.625rem;
        }
        [part="item-checkbox"].checked {
            background: var(--mj-color-brand-default);
            border-color: var(--mj-color-brand-default);
            color: var(--mj-color-text-on-brand);
        }
        [part="item-checkbox"].indeterminate {
            background: var(--mj-color-brand-subtle);
            border-color: var(--mj-color-brand-default);
            color: var(--mj-color-brand-default);
        }
        [part="item-icon"] {
            width: 1rem;
            height: 1rem;
            flex-shrink: 0;
            color: var(--mj-color-text-subtle);
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
            background: var(--mj-color-surface-subtle);
            border-radius: var(--mj-radius-full);
            font-size: var(--mj-font-size-xs);
            color: var(--mj-color-text-subtle);
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
            color: var(--mj-color-text-subtle);
            font-size: var(--mj-font-size-sm);
        }
        [part="empty"] {
            padding: var(--mj-space-4);
            text-align: center;
            color: var(--mj-color-text-subtle);
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
        'single-expand', 'expanded', 'default-expanded'];

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
        this._focusedId = null;
    }

    get nodes() {
        return this._nodes;
    }

    set nodes(val) {
        this._nodes = Array.isArray(val) ? val : [];
        this._renderTree();
    }

    get selectedNodes() {
        const allNodes = this._flattenNodes(this._nodes);
        return allNodes.filter((n) => this._selectedIds.has(n.id));
    }

    get expandedNodeIds() {
        return new Set(this._expandedIds);
    }

    get dataSource() {
        return this._dataSource;
    }

    set dataSource(val) {
        this._dataSource = val;
    }

    render() {
        return `
            <div
                part="tree"
                id="${this._treeId}"
                role="tree"
                tabindex="0"
                aria-label="${this.getAttribute('aria-label') || 'Tree'}"
            >
                <slot></slot>
            </div>
            <div id="${this._liveId}" aria-live="polite" aria-atomic="true" class="sr-only"></div>
        `;
    }

    afterRender() {
        const tree = this.$('[part="tree"]');

        this.listen(tree, 'keydown', (e) => this._onTreeKeydown(e));
        this.listen(tree, 'click', (e) => this._onTreeClick(e));

        // Initialize from nodes property or light DOM
        if (this._nodes.length > 0) {
            this._renderTree();
        } else {
            this._initFromLightDom();
        }

        // Apply default-expanded
        const defaultExpanded = this.getAttribute('default-expanded') || 'root';
        if (defaultExpanded === 'root' && this._nodes.length > 0) {
            this._nodes.forEach((n) => {
                if (n.children != null || n.hasChildren === true) {
                    this._expandedIds.add(n.id);
                }
            });
        }

        // Apply value attribute
        const initialValue = this.getAttribute('value') || '';
        if (initialValue.length > 0) {
            initialValue.split(',').map((v) => v.trim()).filter((v) => v.length > 0).forEach((v) => {
                this._selectedIds.add(v);
            });
        }

        this._renderTree();
    }

    onAttributeChanged(name, oldVal, newVal) {
        if (name === 'value') {
            const ids = (newVal || '').split(',').map((v) => v.trim()).filter((v) => v.length > 0);
            this._selectedIds = new Set(ids);
            this._renderTree();
            this._syncFormValue();
        }
        if (name === 'selection') {
            this._selectedIds.clear();
            this._renderTree();
        }
    }

    _initFromLightDom() {
        const items = this.querySelectorAll(':scope > mj-tree-item');
        this._nodes = this._parseTreeItems(items);
    }

    _parseTreeItems(items) {
        const nodes = [];
        items.forEach((item) => {
            const id = item.getAttribute('node-id') || nextId('mj-tn');
            const label = item.getAttribute('label') || item.textContent.trim();
            const value = item.getAttribute('value') || id;
            const icon = item.getAttribute('icon') || null;
            const badge = item.getAttribute('badge') || null;
            const disabled = item.hasAttribute('disabled');
            const hasChildren = item.hasAttribute('has-children');
            const childItems = item.querySelectorAll(':scope > mj-tree-item');
            const children = childItems.length > 0 ? this._parseTreeItems(childItems) : (hasChildren ? undefined : null);

            nodes.push({ id, label, value, icon, badge, disabled, hasChildren, children });
        });
        return nodes;
    }

    _renderTree() {
        const treeEl = this.$('[part="tree"]');
        if (treeEl == null) {
            return;
        }

        if (this._nodes.length === 0) {
            treeEl.innerHTML = `<div part="empty"><slot name="empty">No items.</slot></div>`;
            return;
        }

        treeEl.innerHTML = this._renderNodes(this._nodes, 1);

        // If no focusedId or no element has tabindex=0, set first item
        if (this._focusedId == null) {
            const firstRow = treeEl.querySelector('.tree-item-row');
            if (firstRow != null) {
                this._focusedId = firstRow.dataset.nodeId;
            }
        }

        this._updateTabindex();
    }

    _renderNodes(nodes, level) {
        const selection = this.getAttribute('selection') || 'single';
        const parts = nodes.map((node, idx) => {
            return this._renderNode(node, level, idx, nodes.length);
        });
        return parts.join('');
    }

    _renderNode(node, level, posInSet, setSize) {
        const selection = this.getAttribute('selection') || 'single';
        const isLeaf = node.children === null && node.hasChildren !== true;
        const isExpanded = this._expandedIds.has(node.id);
        const isSelected = this._selectedIds.has(node.id);
        const isLoading = this._loadingIds.has(node.id);
        const nodeId = nextId('mj-tn-row');

        const toggleClass = isLeaf ? 'leaf' : (isExpanded ? 'expanded' : '');
        const toggleEl = `
            <button
                part="item-toggle"
                class="${toggleClass}"
                tabindex="-1"
                aria-label="${isExpanded ? 'Collapse' : 'Expand'} ${node.label}"
                data-action="toggle"
                data-node-id="${node.id}"
            >›</button>
        `;

        let checkboxHtml = '';
        if (selection === 'checkbox') {
            const checkState = this._getCheckState(node);
            const checkClass = checkState === 'true' ? 'checked' : (checkState === 'mixed' ? 'indeterminate' : '');
            const checkGlyph = checkState === 'true' ? '✓' : (checkState === 'mixed' ? '–' : '');
            checkboxHtml = `
                <span
                    part="item-checkbox"
                    class="${checkClass}"
                    aria-hidden="true"
                >${checkGlyph}</span>
            `;
        }

        const iconHtml = node.icon != null ? `<span part="item-icon" aria-hidden="true">${node.icon}</span>` : '';
        const badgeHtml = node.badge != null ? `<span part="item-badge">${node.badge}</span>` : '';

        let ariaAttrs = `aria-level="${level}" aria-setsize="${setSize}" aria-posinset="${posInSet + 1}"`;
        if (selection === 'checkbox') {
            const checkState = this._getCheckState(node);
            ariaAttrs += ` aria-checked="${checkState}"`;
        } else if (selection === 'single' || selection === 'multi') {
            ariaAttrs += ` aria-selected="${isSelected ? 'true' : 'false'}"`;
        }
        if (!isLeaf) {
            ariaAttrs += ` aria-expanded="${isExpanded ? 'true' : 'false'}"`;
        }
        if (node.disabled === true) {
            ariaAttrs += ` aria-disabled="true"`;
        }

        const rowTabindex = this._focusedId === node.id ? '0' : '-1';

        const rowHtml = `
            <div
                class="tree-item-row"
                role="treeitem"
                id="${nodeId}"
                tabindex="${rowTabindex}"
                data-node-id="${node.id}"
                style="--level: ${level - 1}"
                ${ariaAttrs}
            >
                ${toggleEl}
                ${checkboxHtml}
                ${iconHtml}
                <span part="item-label">${node.label}</span>
                ${badgeHtml}
            </div>
        `;

        let childrenHtml = '';
        if (!isLeaf) {
            let childContent = '';
            if (isLoading) {
                childContent = `<div part="item-loading"><slot name="loading">Loading…</slot></div>`;
            } else if (isExpanded && node.children != null) {
                childContent = this._renderNodes(node.children, level + 1);
            }
            childrenHtml = `
                <div
                    part="item-children"
                    role="group"
                    aria-label="${node.label} children"
                    ${isExpanded ? '' : 'hidden'}
                >${childContent}</div>
            `;
        }

        return `<div part="tree-item">${rowHtml}${childrenHtml}</div>`;
    }

    _getCheckState(node) {
        if (node.children == null || node.children.length === 0) {
            return this._selectedIds.has(node.id) ? 'true' : 'false';
        }
        const allNodes = this._flattenNodes(node.children);
        const enabledNodes = allNodes.filter((n) => n.disabled !== true);
        if (enabledNodes.length === 0) {
            return this._selectedIds.has(node.id) ? 'true' : 'false';
        }
        const selectedCount = enabledNodes.filter((n) => this._selectedIds.has(n.id)).length;
        if (selectedCount === 0) {
            return 'false';
        }
        if (selectedCount === enabledNodes.length) {
            return 'true';
        }
        return 'mixed';
    }

    _flattenNodes(nodes) {
        const result = [];
        const walk = (nodeList) => {
            nodeList.forEach((n) => {
                result.push(n);
                if (n.children != null && n.children.length > 0) {
                    walk(n.children);
                }
            });
        };
        walk(nodes);
        return result;
    }

    _findNode(id, nodes) {
        nodes = nodes || this._nodes;
        for (const node of nodes) {
            if (node.id === id) {
                return node;
            }
            if (node.children != null && node.children.length > 0) {
                const found = this._findNode(id, node.children);
                if (found != null) {
                    return found;
                }
            }
        }
        return null;
    }

    _onTreeClick(e) {
        const row = e.target.closest('.tree-item-row');
        if (row == null) {
            return;
        }
        const nodeId = row.dataset.nodeId;
        const node = this._findNode(nodeId);
        if (node == null) {
            return;
        }

        const toggleBtn = e.target.closest('[data-action="toggle"]');
        if (toggleBtn != null) {
            e.stopPropagation();
            this._toggleExpand(node);
            return;
        }

        if (node.disabled === true) {
            return;
        }

        const selection = this.getAttribute('selection') || 'single';
        if (selection === 'none') {
            this._toggleExpand(node);
            return;
        }

        this._focusedId = nodeId;
        this._updateTabindex();
        row.focus();

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
        const tree = this.$('[part="tree"]');
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
            const node = this._findNode(nodeId);
            if (node == null) {
                return;
            }
            if (!this._expandedIds.has(nodeId) && (node.children != null || node.hasChildren === true)) {
                this._toggleExpand(node);
            } else if (this._expandedIds.has(nodeId)) {
                // Move to first child
                const nextRow = rows[currentIdx + 1];
                if (nextRow != null) {
                    this._setFocusedRow(nextRow);
                }
            }
            return;
        }

        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            const nodeId = this._focusedId;
            const node = this._findNode(nodeId);
            if (node != null && this._expandedIds.has(nodeId)) {
                this._toggleExpand(node);
            } else {
                // Move to parent
                const parentRow = this._findParentRow(nodeId, rows);
                if (parentRow != null) {
                    this._setFocusedRow(parentRow);
                }
            }
            return;
        }

        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            const nodeId = this._focusedId;
            const node = this._findNode(nodeId);
            if (node == null || node.disabled === true) {
                return;
            }
            const selection = this.getAttribute('selection') || 'single';
            if (selection === 'checkbox') {
                this._toggleCheckbox(node);
            } else if (selection === 'single') {
                this._selectSingle(nodeId);
            } else if (selection === 'multi') {
                this._toggleMultiSelect(nodeId);
            } else if (selection === 'none') {
                this._toggleExpand(node);
            }
            return;
        }

        if (e.key === '*') {
            e.preventDefault();
            this._expandAllSiblings();
            return;
        }

        // Type-ahead
        if (e.key.length === 1 && !e.ctrlKey && !e.metaKey) {
            clearTimeout(this._typeaheadTimer);
            this._typeaheadBuffer += e.key.toLowerCase();
            this._typeaheadTimer = setTimeout(() => {
                this._typeaheadBuffer = '';
            }, 500);

            const collator = new Intl.Collator(undefined, { sensitivity: 'base' });
            const startIdx = currentIdx >= 0 ? currentIdx + 1 : 0;
            const searchOrder = [...rows.slice(startIdx), ...rows.slice(0, startIdx)];
            const match = searchOrder.find((r) => {
                const nodeId = r.dataset.nodeId;
                const node = this._findNode(nodeId);
                if (node == null) {
                    return false;
                }
                return node.label.toLowerCase().startsWith(this._typeaheadBuffer);
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

    _updateTabindex() {
        const treeEl = this.$('[part="tree"]');
        if (treeEl == null) {
            return;
        }
        const rows = treeEl.querySelectorAll('.tree-item-row');
        rows.forEach((row) => {
            row.tabIndex = row.dataset.nodeId === this._focusedId ? 0 : -1;
        });
        // If focused row exists, update tabindex=0 on the tree container too
        if (this._focusedId != null) {
            treeEl.tabIndex = -1;
        } else {
            treeEl.tabIndex = 0;
        }
    }

    _findParentRow(nodeId, rows) {
        // Find the parent by DOM structure — the closest ancestor .tree-item-row
        const treeEl = this.$('[part="tree"]');
        if (treeEl == null) {
            return null;
        }
        const childRow = treeEl.querySelector(`.tree-item-row[data-node-id="${nodeId}"]`);
        if (childRow == null) {
            return null;
        }
        let el = childRow.parentElement;
        while (el != null && el !== treeEl) {
            if (el.classList.contains('tree-item-row')) {
                return el;
            }
            if (el.getAttribute('part') === 'item-children') {
                const parent = el.previousElementSibling;
                if (parent != null && parent.classList.contains('tree-item-row')) {
                    return parent;
                }
            }
            el = el.parentElement;
        }
        return null;
    }

    async _toggleExpand(node) {
        if (this._expandedIds.has(node.id)) {
            // Collapse
            this._expandedIds.delete(node.id);
            this._renderTree();
            announce(`${node.label} collapsed`, 'polite');
            this.emit('mj-collapse', { nodeId: node.id, node });
            return;
        }

        // Expand
        const expandEvent = this.emit('mj-expand', { nodeId: node.id, node }, { cancelable: true });
        if (expandEvent.defaultPrevented) {
            return;
        }

        this._expandedIds.add(node.id);

        // Async children
        if (node.hasChildren === true && (node.children == null || node.children.length === 0)) {
            if (this._dataSource != null) {
                this._loadingIds.add(node.id);
                this._renderTree();
                announce(`Loading ${node.label} children`, 'polite');
                this.emit('mj-node-load-start', { nodeId: node.id });

                try {
                    const children = await this._dataSource.getChildren(node.id);
                    node.children = Array.isArray(children) ? children : [];
                    this._loadingIds.delete(node.id);
                    this._renderTree();
                    announce(`Loaded ${node.children.length} items`, 'polite');
                    this.emit('mj-node-load-end', { nodeId: node.id, children: node.children });
                } catch (err) {
                    node.children = [];
                    this._loadingIds.delete(node.id);
                    this._renderTree();
                    this.emit('mj-node-error', { nodeId: node.id, error: err });
                }
                return;
            }
        }

        // Single-expand mode
        if (this.hasAttribute('single-expand')) {
            const parent = this._findParentNode(node.id, this._nodes);
            const siblings = parent != null ? parent.children : this._nodes;
            if (siblings != null) {
                siblings.forEach((sibling) => {
                    if (sibling.id !== node.id) {
                        this._expandedIds.delete(sibling.id);
                    }
                });
            }
        }

        this._renderTree();
        announce(`${node.label} expanded`, 'polite');
    }

    _findParentNode(nodeId, nodes, parent) {
        for (const node of nodes) {
            if (node.children != null) {
                if (node.children.some((c) => c.id === nodeId)) {
                    return node;
                }
                const found = this._findParentNode(nodeId, node.children, node);
                if (found != null) {
                    return found;
                }
            }
        }
        return null;
    }

    _selectSingle(nodeId) {
        const prevSelected = new Set(this._selectedIds);
        this._selectedIds.clear();
        this._selectedIds.add(nodeId);

        if (!this._setsEqual(prevSelected, this._selectedIds)) {
            this._renderTree();
            this._syncFormValue();
            this._emitChange();
        }
    }

    _toggleMultiSelect(nodeId) {
        if (this._selectedIds.has(nodeId)) {
            this._selectedIds.delete(nodeId);
        } else {
            this._selectedIds.add(nodeId);
        }
        this._renderTree();
        this._syncFormValue();
        this._emitChange();
    }

    _selectRange(endNodeId) {
        const rows = this._getVisibleRows();
        const startIdx = rows.findIndex((r) => {
            return Array.from(this._selectedIds).some((id) => r.dataset.nodeId === id);
        });
        const endIdx = rows.findIndex((r) => r.dataset.nodeId === endNodeId);

        if (startIdx < 0 || endIdx < 0) {
            this._toggleMultiSelect(endNodeId);
            return;
        }

        const lo = Math.min(startIdx, endIdx);
        const hi = Math.max(startIdx, endIdx);
        rows.slice(lo, hi + 1).forEach((r) => this._selectedIds.add(r.dataset.nodeId));

        this._renderTree();
        this._syncFormValue();
        this._emitChange();
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

        this._renderTree();
        this._syncFormValue();
        this._emitChange();
    }

    _setCheckRecursive(node, checked) {
        if (node.disabled === true) {
            return;
        }
        if (checked) {
            this._selectedIds.add(node.id);
        } else {
            this._selectedIds.delete(node.id);
        }
        if (node.children != null && node.children.length > 0) {
            node.children.forEach((child) => this._setCheckRecursive(child, checked));
        }
    }

    _expandAllSiblings() {
        const nodeId = this._focusedId;
        if (nodeId == null) {
            return;
        }
        const parentNode = this._findParentNode(nodeId, this._nodes);
        const siblings = parentNode != null ? parentNode.children : this._nodes;
        if (siblings == null) {
            return;
        }
        siblings.forEach((sibling) => {
            if (sibling.children != null || sibling.hasChildren === true) {
                this._expandedIds.add(sibling.id);
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
        const values = selectedNodes.map((n) => n.value || n.id);
        this.emit('mj-change', { values, selectedNodes });
    }

    _syncFormValue() {
        const fd = new FormData();
        const name = this.getAttribute('name') || '';
        const selection = this.getAttribute('selection') || 'single';

        if (name.length > 0 && selection !== 'none') {
            this.selectedNodes.forEach((n) => fd.append(name, n.value || n.id));
        }

        this._setFormValue(fd);
        this._customValidity(this._computeValidity());
    }

    _computeValidity() {
        const required = this.hasAttribute('required');
        const selection = this.getAttribute('selection') || 'single';
        if (required && selection !== 'none' && this._selectedIds.size === 0) {
            return 'Please select at least one item.';
        }
        return '';
    }

    formResetCallback() {
        this._selectedIds.clear();
        const initialValue = this.getAttribute('value') || '';
        initialValue.split(',').map((v) => v.trim()).filter((v) => v.length > 0).forEach((v) => {
            this._selectedIds.add(v);
        });

        this._expandedIds.clear();
        const defaultExpanded = this.getAttribute('default-expanded') || 'root';
        if (defaultExpanded === 'root') {
            this._nodes.forEach((n) => {
                if (n.children != null || n.hasChildren === true) {
                    this._expandedIds.add(n.id);
                }
            });
        }

        this._renderTree();
        this._syncFormValue();
    }
}
