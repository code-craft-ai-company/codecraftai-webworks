/*
 * explorer-model.js
 *
 * The data side of the API explorer (layout C: a tree of APIs by path, and a few pinned panes). Everything in this file is a pure function
 * over an OpenAPI document: no DOM, no network, no Swagger UI. explorer.js draws the page from it, and the unit tests run it under node.
 *
 *   - operations      one row per method on a path, with the words the path puts it under
 *   - the tree        those words as nested groups; a chain of groups with a single child folds into one (``projects / rpa``)
 *   - the query       the search box: every term must match, a term that names a method filters by method
 *   - the address     which APIs are pinned, which panes are folded and what was searched, kept in the page address so a link shares them
 *   - a pane document the OpenAPI document cut down to one operation (and the components it uses), which a pane gives Swagger UI
 */
(function (root, factory) {
    "use strict";
    var model = factory();
    if (typeof module === "object" && module.exports) {
        module.exports = model;
    } else {
        root.CCAIApiExplorerModel = model;
    }
}(typeof self !== "undefined" ? self : this, function () {
    "use strict";

    /* The members of an OpenAPI path item that are operations, in the order a page lists them. */
    var METHODS = ["get", "post", "put", "patch", "delete", "options", "head", "trace"];

    /* The component sections a $ref may point into. securitySchemes are named by security requirements, not by $ref, so they are kept whole. */
    var REFERENCED_SECTIONS = ["schemas", "parameters", "responses", "requestBodies", "headers", "examples", "links", "callbacks", "pathItems"];

    var COMPONENT_REF = /^#\/components\/([^/]+)\/(.+)$/;

    var ROOT_NAME = "(root)";

    function methodRank(method) {
        var index = METHODS.indexOf(method.toLowerCase());
        return index < 0 ? METHODS.length : index;
    }

    function compareText(left, right) {
        return left < right ? -1 : (left > right ? 1 : 0);
    }

    /* ---- Path to place ------------------------------------------------------------------------------------------------------------------ */

    /*
     * The places a path puts an operation under. A path parameter (``{project_id}``) names no place and is skipped. An action on an item or a
     * collection (``{id}:start``, ``clients:inventory``) is a place of its own under the item or collection it acts on (``:start``).
     *
     * Each piece carries ``after``: the text of the path that follows it, which is what a row shows beside the group it sits in.
     */
    function splitPath(path) {
        var raw = String(path).split("/").filter(function (segment) { return segment.length > 0; });
        var pieces = [];

        raw.forEach(function (segment, index) {
            var tail = raw.length > index + 1 ? "/" + raw.slice(index + 1).join("/") : "";
            var isParameter = segment.charAt(0) === "{";
            var text = isParameter ? segment.slice(segment.indexOf("}") + 1) : segment;
            var name = text;
            var action = "";
            var colon = text.indexOf(":");

            if (colon === 0) {
                name = "";
                action = text.slice(1);
            } else if (colon > 0) {
                name = text.slice(0, colon);
                action = text.slice(colon + 1);
            }

            if (!isParameter && name.length > 0) {
                pieces.push({ name: name, after: (action.length > 0 ? ":" + action : "") + tail });
            }
            if (action.length > 0) {
                pieces.push({ name: ":" + action, after: tail });
            }
        });

        if (pieces.length === 0) {
            pieces.push({ name: ROOT_NAME, after: path === "/" ? "" : String(path) });
        }

        return pieces;
    }

    /* ---- Operations --------------------------------------------------------------------------------------------------------------------- */

    /*
     * Every operation of a document as a row, sorted by path then by method. A row keeps the document's own operation and path item so a pane
     * can be cut from them.
     */
    function buildOperations(document) {
        var paths = (document && document.paths) || {};
        var rtnval = [];

        Object.keys(paths).forEach(function (path) {
            var item = paths[path];
            if (!item || typeof item !== "object") {
                return;
            }
            METHODS.forEach(function (method) {
                var operation = item[method];
                if (!operation || typeof operation !== "object") {
                    return;
                }
                var upper = method.toUpperCase();
                var tags = Array.isArray(operation.tags) ? operation.tags.map(String) : [];
                var summary = operation.summary ? String(operation.summary) : "";
                var operationId = operation.operationId ? String(operation.operationId) : "";
                rtnval.push({
                    key: upper + " " + path,
                    method: upper,
                    path: path,
                    summary: summary,
                    operationId: operationId,
                    tags: tags,
                    deprecated: operation.deprecated === true,
                    pieces: splitPath(path),
                    search: [upper, path, summary, operationId, tags.join(" ")].join(" ").toLowerCase(),
                    operation: operation,
                    pathItem: item
                });
            });
        });

        rtnval.sort(function (left, right) {
            return compareText(left.path, right.path) || (methodRank(left.method) - methodRank(right.method));
        });

        return rtnval;
    }

    function operationKey(method, path) {
        return String(method).toUpperCase() + " " + path;
    }

    function operationsByKey(operations) {
        var rtnval = {};
        operations.forEach(function (op) { rtnval[op.key] = op; });
        return rtnval;
    }

    /* ---- Tree --------------------------------------------------------------------------------------------------------------------------- */

    function newNode(name, id, depth) {
        return { name: name, id: id, depth: depth, kids: {}, children: [], ops: [], count: 0 };
    }

    /*
     * The operations as nested groups. A group with one child group and no operations of its own folds into that child (``projects / rpa``), the
     * top level excepted, so a long chain reads as one step. ``depth`` is how many path words the group stands for; ``id`` is stable for a
     * document and names the group in the page's open/closed state.
     */
    function buildTree(operations) {
        var root = newNode("", "", 0);

        operations.forEach(function (op) {
            var node = root;
            op.pieces.forEach(function (piece, index) {
                if (!node.kids[piece.name]) {
                    node.kids[piece.name] = newNode(piece.name, node.id + "/" + piece.name, index + 1);
                }
                node = node.kids[piece.name];
            });
            node.ops.push(op);
        });

        function finish(node, isRoot) {
            var names = Object.keys(node.kids);
            while (!isRoot && names.length === 1 && node.ops.length === 0) {
                var only = node.kids[names[0]];
                node.name = node.name + " / " + only.name;
                node.id = only.id;
                node.depth = only.depth;
                node.kids = only.kids;
                node.ops = only.ops;
                names = Object.keys(node.kids);
            }
            node.children = Object.keys(node.kids).sort().map(function (name) {
                return finish(node.kids[name], false);
            });
            node.count = node.ops.length + node.children.reduce(function (sum, child) { return sum + child.count; }, 0);
            return node;
        }

        return finish(root, true);
    }

    /* The ids of the groups, outermost first, that lead to an operation (so the page can open them). */
    function groupIdsFor(root, key) {
        function walk(node, trail) {
            for (var i = 0; i < node.ops.length; i++) {
                if (node.ops[i].key === key) {
                    return trail;
                }
            }
            for (var j = 0; j < node.children.length; j++) {
                var child = node.children[j];
                var found = walk(child, trail.concat([child.id]));
                if (found) {
                    return found;
                }
            }
            return null;
        }
        return walk(root, []) || [];
    }

    /* A copy of the tree holding only the operations the predicate accepts; groups left empty are dropped and the counts follow. */
    function pruneTree(root, predicate) {
        function copy(node) {
            var rtnval = newNode(node.name, node.id, node.depth);
            rtnval.ops = node.ops.filter(predicate);
            rtnval.children = node.children.map(copy).filter(function (child) { return child.count > 0; });
            rtnval.count = rtnval.ops.length + rtnval.children.reduce(function (sum, child) { return sum + child.count; }, 0);
            return rtnval;
        }
        return copy(root);
    }

    /* What a row shows beside the group it sits in: the part of its path the group's own name does not already say. */
    function restOf(op, node) {
        var index = Math.min(node.depth, op.pieces.length) - 1;
        return index < 0 ? op.path : op.pieces[index].after;
    }

    /* ---- Search ------------------------------------------------------------------------------------------------------------------------- */

    /* The terms of a search box: lower case, split on spaces. */
    function parseQuery(text) {
        return String(text || "").toLowerCase().split(/\s+/).filter(function (term) { return term.length > 0; });
    }

    /* Every term must match. A term that is a method name (``get``) matches that method only; any other term matches anywhere in the row. */
    function matches(op, terms) {
        for (var i = 0; i < terms.length; i++) {
            var term = terms[i];
            if (METHODS.indexOf(term) >= 0) {
                if (op.method.toLowerCase() !== term) {
                    return false;
                }
            } else if (op.search.indexOf(term) < 0) {
                return false;
            }
        }
        return true;
    }

    /* ---- Page address ------------------------------------------------------------------------------------------------------------------- */

    /* Which APIs are pinned, which panes are folded and what was searched, from a page address's fragment (with or without the ``#``). */
    function parseHash(hash) {
        var text = String(hash || "").replace(/^#/, "");
        var params = new URLSearchParams(text);
        var pins = [];
        params.getAll("pin").forEach(function (key) {
            if (key.length > 0 && pins.indexOf(key) < 0) {
                pins.push(key);
            }
        });
        var folds = params.getAll("fold").filter(function (key) { return pins.indexOf(key) >= 0; });
        return { pins: pins, folds: folds, query: params.get("q") || "" };
    }

    function encodePart(text) {
        return encodeURIComponent(text).replace(/%2F/g, "/").replace(/%7B/g, "{").replace(/%7D/g, "}").replace(/%3A/g, ":").replace(/%20/g, "+");
    }

    /* The fragment (without the ``#``) for a state: pins in order, then the folded ones, then the search. Empty when there is nothing to keep. */
    function buildHash(state) {
        var parts = [];
        (state.pins || []).forEach(function (key) { parts.push("pin=" + encodePart(key)); });
        (state.folds || []).forEach(function (key) {
            if ((state.pins || []).indexOf(key) >= 0) {
                parts.push("fold=" + encodePart(key));
            }
        });
        if (state.query) {
            parts.push("q=" + encodePart(state.query));
        }
        return parts.join("&");
    }

    /* ---- One operation as a document ---------------------------------------------------------------------------------------------------- */

    function collectRefs(value, found) {
        if (Array.isArray(value)) {
            value.forEach(function (item) { collectRefs(item, found); });
        } else if (value && typeof value === "object") {
            Object.keys(value).forEach(function (name) {
                var member = value[name];
                if (name === "$ref" && typeof member === "string") {
                    found.push(member);
                } else {
                    collectRefs(member, found);
                }
            });
        }
        return found;
    }

    function unescapePointer(text) {
        return text.replace(/~1/g, "/").replace(/~0/g, "~");
    }

    /* The components a set of values reaches through $ref, and the ones those reach in turn, and nothing else. */
    function reachableComponents(components, roots) {
        var rtnval = {};
        var seen = {};
        var queue = collectRefs(roots, []);

        while (queue.length > 0) {
            var ref = queue.shift();
            if (seen[ref]) {
                continue;
            }
            seen[ref] = true;

            var parts = COMPONENT_REF.exec(ref);
            if (!parts || !components) {
                continue;
            }
            var section = parts[1];
            var name = unescapePointer(parts[2]);
            if (REFERENCED_SECTIONS.indexOf(section) < 0 || !components[section] || !(name in components[section])) {
                continue;
            }
            if (!rtnval[section]) {
                rtnval[section] = {};
            }
            rtnval[section][name] = components[section][name];
            queue = queue.concat(collectRefs(components[section][name], []));
        }

        return rtnval;
    }

    /*
     * The document a pane gives Swagger UI: the same ``openapi``, ``info``, ``servers`` and ``security`` (so the request goes where the full page's
     * would), one path holding one operation, and only the components that operation reaches. Nothing in the input is changed.
     */
    function buildPaneDocument(document, op) {
        var item = {};
        ["summary", "description", "servers", "parameters"].forEach(function (name) {
            if (op.pathItem[name] !== undefined) {
                item[name] = op.pathItem[name];
            }
        });

        var operation = {};
        Object.keys(op.operation).forEach(function (name) {
            if (name !== "tags") {
                operation[name] = op.operation[name];
            }
        });
        item[op.method.toLowerCase()] = operation;

        var paths = {};
        paths[op.path] = item;

        var rtnval = { openapi: document.openapi, info: document.info, paths: paths };
        ["jsonSchemaDialect", "servers", "security"].forEach(function (name) {
            if (document[name] !== undefined) {
                rtnval[name] = document[name];
            }
        });

        var components = reachableComponents(document.components, paths);
        if (document.components && document.components.securitySchemes) {
            components.securitySchemes = document.components.securitySchemes;
        }
        if (Object.keys(components).length > 0) {
            rtnval.components = components;
        }

        return JSON.parse(JSON.stringify(rtnval));
    }

    return {
        METHODS: METHODS,
        ROOT_NAME: ROOT_NAME,
        splitPath: splitPath,
        buildOperations: buildOperations,
        operationKey: operationKey,
        operationsByKey: operationsByKey,
        buildTree: buildTree,
        groupIdsFor: groupIdsFor,
        pruneTree: pruneTree,
        restOf: restOf,
        parseQuery: parseQuery,
        matches: matches,
        parseHash: parseHash,
        buildHash: buildHash,
        reachableComponents: reachableComponents,
        buildPaneDocument: buildPaneDocument
    };
}));
