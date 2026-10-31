/*
 * explorer.js
 *
 * The API explorer page: a tree of the document's APIs by path on the left and, on the right, the APIs a person has pinned, each in a pane of
 * its own that folds and unfolds by itself. A pane shows its operation with the Swagger UI that ships with this package, so **Try it out**
 * sends the request exactly as the Swagger UI page does (same origin, as the signed-in person).
 *
 * The page holds no inline script, so it works under a Content-Security-Policy that allows scripts from its own origin only. The starter
 * script (explorer-initializer.js) calls CCAIApiExplorer.start(config) with:
 *
 *   documentUrl            where to read the OpenAPI document from
 *   title                  the API's name
 *   supportedSubmitMethods the methods Try it out may send (lower case); omitted for every method, empty for none
 *   tryItOutEnabled        open each pane already in Try it out mode (default false: click Try it out, then Execute)
 *
 * The page address keeps the pinned APIs, the folded panes and the search (``#pin=GET /projects&pin=...&fold=...&q=...``), so a link shares a
 * working set. explorer-model.js holds everything that does not touch the page.
 */
(function (root) {
    "use strict";

    var Model = root.CCAIApiExplorerModel;

    function escapeHtml(text) {
        return String(text === null || text === undefined ? "" : text).replace(/[&<>"']/g, function (character) {
            return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[character];
        });
    }

    /* A path with its {parameters} marked, as HTML. */
    function pathHtml(path) {
        return escapeHtml(path).replace(/\{[^}]*\}/g, function (parameter) {
            return "<span class=\"param\">" + parameter + "</span>";
        });
    }

    function methodChip(method) {
        return "<span class=\"m m-" + escapeHtml(method) + "\">" + escapeHtml(method) + "</span>";
    }

    function Explorer(rootElement, config) {
        this.rootElement = rootElement;
        this.config = config;
        this.title = config.title || "API explorer";
        this.operations = [];
        this.byKey = {};
        this.tree = null;
        this.openGroups = {};
        this.query = "";
        this.pins = [];
        this.folds = [];
        this.panes = {};
        this.missing = [];
        this.paneCounter = 0;
    }

    /* ---- Loading ------------------------------------------------------------------------------------------------------------------------ */

    Explorer.prototype.load = function () {
        var self = this;
        this.rootElement.innerHTML = "<p class=\"status\" role=\"status\">Loading the API document&hellip;</p>";

        return root.fetch(this.config.documentUrl, { credentials: "same-origin", headers: { "Accept": "application/json" } })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("the server answered " + response.status);
                }
                return response.json();
            })
            .then(function (document) {
                self.document = document;
                self.operations = Model.buildOperations(document);
                self.byKey = Model.operationsByKey(self.operations);
                self.tree = Model.buildTree(self.operations);
                self.build();
            })
            .catch(function (error) {
                self.rootElement.innerHTML =
                    "<div class=\"status status-error\" role=\"alert\"><p>The API document could not be loaded: " + escapeHtml(error.message) +
                    ".</p><p>If you were signed out, sign in again and reload this page.</p><button type=\"button\" class=\"btn\" id=\"explorer-retry\">Try again</button></div>";
                var retry = self.rootElement.querySelector("#explorer-retry");
                if (retry) {
                    retry.addEventListener("click", function () { self.load(); });
                }
            });
    };

    /* ---- The page ----------------------------------------------------------------------------------------------------------------------- */

    Explorer.prototype.build = function () {
        var pathCount = {};
        this.operations.forEach(function (op) { pathCount[op.path] = true; });

        this.rootElement.innerHTML =
            "<header class=\"bar\">" +
                "<h1>" + escapeHtml(this.title) + "</h1>" +
                "<span class=\"bar-stat\">" + this.operations.length + " APIs on " + Object.keys(pathCount).length + " paths</span>" +
                "<a class=\"bar-link\" href=\"" + escapeHtml(this.config.documentUrl) + "\">OpenAPI document</a>" +
            "</header>" +
            "<div class=\"bench\">" +
                "<aside class=\"side\" aria-label=\"APIs\">" +
                    "<div class=\"search\">" +
                        "<label for=\"explorer-search\" class=\"label\">Find an API</label>" +
                        "<input id=\"explorer-search\" type=\"search\" autocomplete=\"off\" spellcheck=\"false\" placeholder=\"Path, summary, tag or method\">" +
                        "<small id=\"explorer-hint\"></small>" +
                    "</div>" +
                    "<nav class=\"tree\" id=\"explorer-tree\" aria-label=\"APIs by path\"></nav>" +
                "</aside>" +
                "<main class=\"main\" id=\"explorer-main\">" +
                    "<div class=\"toolbar\" id=\"explorer-toolbar\" hidden>" +
                        "<span id=\"explorer-count\" class=\"toolbar-count\"></span>" +
                        "<button type=\"button\" class=\"btn\" data-action=\"fold-all\">Fold all</button>" +
                        "<button type=\"button\" class=\"btn\" data-action=\"unfold-all\">Unfold all</button>" +
                        "<button type=\"button\" class=\"btn\" data-action=\"unpin-all\">Unpin all</button>" +
                    "</div>" +
                    "<p class=\"notice\" id=\"explorer-notice\" role=\"status\" hidden></p>" +
                    "<div class=\"panes\" id=\"explorer-panes\"></div>" +
                    "<div class=\"empty\" id=\"explorer-empty\">" +
                        "<h2>Pin the APIs you want to work with</h2>" +
                        "<p>Open a group in the list and tick an API. It opens here in a pane of its own, with its parameters, its responses and Try it out. " +
                        "Pin as many as you like and fold the ones you are done with; the address of this page keeps them, so you can send it to someone.</p>" +
                    "</div>" +
                "</main>" +
            "</div>";

        this.searchInput = this.rootElement.querySelector("#explorer-search");
        this.treeElement = this.rootElement.querySelector("#explorer-tree");
        this.hintElement = this.rootElement.querySelector("#explorer-hint");
        this.panesElement = this.rootElement.querySelector("#explorer-panes");
        this.emptyElement = this.rootElement.querySelector("#explorer-empty");
        this.toolbarElement = this.rootElement.querySelector("#explorer-toolbar");
        this.countElement = this.rootElement.querySelector("#explorer-count");
        this.noticeElement = this.rootElement.querySelector("#explorer-notice");

        this.wire();
        this.applyAddress(root.location.hash, false);
    };

    Explorer.prototype.wire = function () {
        var self = this;

        this.searchInput.addEventListener("input", function () {
            self.query = self.searchInput.value;
            self.renderTree();
            self.writeAddress(false);
        });
        this.searchInput.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && self.searchInput.value.length > 0) {
                self.searchInput.value = "";
                self.query = "";
                self.renderTree();
                self.writeAddress(false);
            }
        });

        this.treeElement.addEventListener("click", function (event) {
            var group = event.target.closest("[data-group]");
            var row = event.target.closest("[data-op]");
            if (group) {
                self.toggleGroup(group.getAttribute("data-group"));
            } else if (row) {
                self.togglePin(row.getAttribute("data-op"));
            }
        });

        this.rootElement.querySelector("#explorer-toolbar").addEventListener("click", function (event) {
            var button = event.target.closest("[data-action]");
            if (!button) {
                return;
            }
            var action = button.getAttribute("data-action");
            if (action === "fold-all") {
                self.folds = self.pins.slice();
                self.syncPanes();
                self.writeAddress(false);
            } else if (action === "unfold-all") {
                self.folds = [];
                self.syncPanes();
                self.writeAddress(false);
            } else if (action === "unpin-all") {
                self.pins = [];
                self.folds = [];
                self.syncPanes();
                self.renderTree();
                self.writeAddress(true);
            }
        });

        this.panesElement.addEventListener("click", function (event) {
            var pane = event.target.closest("[data-pane]");
            if (!pane) {
                return;
            }
            var key = pane.getAttribute("data-pane");
            if (event.target.closest("[data-fold]")) {
                self.toggleFold(key);
            } else if (event.target.closest("[data-unpin]")) {
                self.togglePin(key);
            }
        });

        root.addEventListener("hashchange", function () { self.applyAddress(root.location.hash, true); });

        root.document.addEventListener("keydown", function (event) {
            var target = event.target;
            var typing = target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.tagName === "SELECT" || target.isContentEditable);
            if (event.key === "/" && !typing && !event.ctrlKey && !event.metaKey && !event.altKey) {
                event.preventDefault();
                self.searchInput.focus();
                self.searchInput.select();
            }
        });
    };

    /* ---- The page address --------------------------------------------------------------------------------------------------------------- */

    /* Make the page match an address's fragment: the pinned APIs (those the document does not have are reported), the folds and the search. */
    Explorer.prototype.applyAddress = function (hash, fromNavigation) {
        var state = Model.parseHash(hash);
        var known = [];
        var unknown = [];
        var self = this;

        state.pins.forEach(function (key) {
            (self.byKey[key] ? known : unknown).push(key);
        });

        this.pins = known;
        this.folds = state.folds.filter(function (key) { return known.indexOf(key) >= 0; });
        this.missing = unknown;
        this.query = state.query;
        this.searchInput.value = state.query;

        known.forEach(function (key) { self.openGroupsFor(key); });
        this.syncPanes();
        this.renderTree();

        if (fromNavigation) {
            this.scrollTreeToPinned();
        }
    };

    /* Write the state into the address. A change to the set of pinned APIs is a step in the history (Back undoes it); folds and searches are not. */
    Explorer.prototype.writeAddress = function (asStep) {
        var fragment = Model.buildHash({ pins: this.pins, folds: this.folds, query: this.query });
        var address = root.location.pathname + root.location.search + (fragment.length > 0 ? "#" + fragment : "");
        if (root.location.hash.replace(/^#/, "") === fragment) {
            return;
        }
        try {
            if (asStep) {
                root.history.pushState(null, "", address);
            } else {
                root.history.replaceState(null, "", address);
            }
        } catch (error) {
            /* A page opened where history is not available simply does not keep its state in the address. */
        }
    };

    /* ---- The tree ----------------------------------------------------------------------------------------------------------------------- */

    Explorer.prototype.openGroupsFor = function (key) {
        var self = this;
        Model.groupIdsFor(this.tree, key).forEach(function (id) { self.openGroups[id] = true; });
    };

    Explorer.prototype.toggleGroup = function (id) {
        this.openGroups[id] = !this.openGroups[id];
        this.renderTree("g:" + id);
    };

    Explorer.prototype.renderTree = function (focusToken) {
        var self = this;
        var terms = Model.parseQuery(this.query);
        var searching = terms.length > 0;
        var tree = searching ? Model.pruneTree(this.tree, function (op) { return Model.matches(op, terms); }) : this.tree;

        if (focusToken === undefined && this.treeElement.contains(root.document.activeElement)) {
            var active = root.document.activeElement;
            if (active.getAttribute("data-group") !== null) {
                focusToken = "g:" + active.getAttribute("data-group");
            } else if (active.getAttribute("data-op") !== null) {
                focusToken = "o:" + active.getAttribute("data-op");
            }
        }

        function groupHtml(node) {
            var open = searching || !!self.openGroups[node.id];
            var html = "<li><button type=\"button\" class=\"group\" data-group=\"" + escapeHtml(node.id) + "\" aria-expanded=\"" + (open ? "true" : "false") + "\">" +
                "<span class=\"chev\" aria-hidden=\"true\"></span><span class=\"group-name\">" + escapeHtml(node.name) + "</span>" +
                "<span class=\"count\">" + node.count + "</span></button>";
            if (open) {
                html += "<ul>" + node.children.map(groupHtml).join("") + node.ops.map(function (op) { return rowHtml(op, node); }).join("") + "</ul>";
            }
            return html + "</li>";
        }

        function rowHtml(op, node) {
            var pinned = self.pins.indexOf(op.key) >= 0;
            var rest = Model.restOf(op, node);
            return "<li><button type=\"button\" class=\"row\" data-op=\"" + escapeHtml(op.key) + "\" aria-pressed=\"" + (pinned ? "true" : "false") + "\">" +
                "<span class=\"row-first\"><span class=\"pin\" aria-hidden=\"true\"></span>" + methodChip(op.method) + "</span>" +
                "<span class=\"row-summary\">" + escapeHtml(op.summary || op.path) + (op.deprecated ? " <span class=\"tag-deprecated\">deprecated</span>" : "") + "</span>" +
                (rest.length > 0 ? "<span class=\"row-rest\">" + pathHtml(rest) + "</span>" : "") +
                "</button></li>";
        }

        if (tree.count === 0) {
            this.treeElement.innerHTML = "<p class=\"none\">No API matches &ldquo;" + escapeHtml(this.query) + "&rdquo;.</p>";
        } else {
            this.treeElement.innerHTML = "<ul class=\"top\">" + tree.children.map(groupHtml).join("") + "</ul>";
        }

        this.hintElement.textContent = searching
            ? tree.count + " of " + this.operations.length + " APIs match"
            : this.operations.length + " APIs in " + this.tree.children.length + " groups";

        if (focusToken) {
            var kind = focusToken.charAt(0) === "g" ? "data-group" : "data-op";
            var wanted = focusToken.slice(2);
            var candidates = this.treeElement.querySelectorAll("[" + kind + "]");
            for (var i = 0; i < candidates.length; i++) {
                if (candidates[i].getAttribute(kind) === wanted) {
                    candidates[i].focus();
                    break;
                }
            }
        }
    };

    Explorer.prototype.scrollTreeToPinned = function () {
        var first = this.treeElement.querySelector("[aria-pressed=\"true\"]");
        if (first && first.scrollIntoView) {
            first.scrollIntoView({ block: "nearest" });
        }
    };

    /* ---- Pins and panes ----------------------------------------------------------------------------------------------------------------- */

    Explorer.prototype.togglePin = function (key) {
        var index = this.pins.indexOf(key);
        var added = index < 0;

        if (added) {
            this.pins.push(key);
        } else {
            this.pins.splice(index, 1);
            this.folds = this.folds.filter(function (folded) { return folded !== key; });
        }

        this.syncPanes();
        this.renderTree(added ? "o:" + key : undefined);
        this.writeAddress(true);

        if (added && this.panes[key]) {
            var pane = this.panes[key].element;
            if (pane.scrollIntoView) {
                pane.scrollIntoView({ block: "start", behavior: "smooth" });
            }
        }
    };

    Explorer.prototype.toggleFold = function (key) {
        var index = this.folds.indexOf(key);
        if (index < 0) {
            this.folds.push(key);
        } else {
            this.folds.splice(index, 1);
        }
        this.syncPanes();
        this.writeAddress(false);
    };

    /* Make the panes match the pins: add the new ones in pin order, remove the unpinned, and fold or unfold the rest. Existing panes are not redrawn,
     * so what was typed into a Try it out form stays. */
    Explorer.prototype.syncPanes = function () {
        var self = this;

        Object.keys(this.panes).forEach(function (key) {
            if (self.pins.indexOf(key) < 0) {
                self.panes[key].element.parentNode.removeChild(self.panes[key].element);
                delete self.panes[key];
            }
        });

        this.pins.forEach(function (key, position) {
            if (!self.panes[key]) {
                self.panes[key] = self.createPane(self.byKey[key]);
            }
            var element = self.panes[key].element;
            if (self.panesElement.children[position] !== element) {
                self.panesElement.insertBefore(element, self.panesElement.children[position] || null);
            }
            self.setFolded(key, self.folds.indexOf(key) >= 0);
        });

        this.emptyElement.hidden = this.pins.length > 0;
        this.toolbarElement.hidden = this.pins.length === 0;
        this.countElement.textContent = this.pins.length + (this.pins.length === 1 ? " API pinned" : " APIs pinned");

        if (this.missing.length > 0) {
            this.noticeElement.hidden = false;
            this.noticeElement.textContent = this.missing.length === 1
                ? "The link named an API this document does not have: " + this.missing[0]
                : "The link named " + this.missing.length + " APIs this document does not have, for example " + this.missing[0];
        } else {
            this.noticeElement.hidden = true;
        }
    };

    Explorer.prototype.createPane = function (op) {
        this.paneCounter += 1;
        var bodyId = "explorer-pane-body-" + this.paneCounter;
        var element = root.document.createElement("section");

        element.className = "pane";
        element.setAttribute("data-pane", op.key);
        element.setAttribute("aria-label", op.key);
        element.innerHTML =
            "<header class=\"pane-head\">" +
                "<button type=\"button\" class=\"pane-fold\" data-fold aria-expanded=\"true\" aria-controls=\"" + bodyId + "\" title=\"Fold or unfold\">" +
                    "<span class=\"chev\" aria-hidden=\"true\"></span><span class=\"sr\">Fold or unfold " + escapeHtml(op.key) + "</span></button>" +
                methodChip(op.method) +
                "<span class=\"pane-title\"><span class=\"pane-path\">" + pathHtml(op.path) + "</span>" +
                (op.summary.length > 0 ? "<span class=\"pane-summary\">" + escapeHtml(op.summary) + "</span>" : "") + "</span>" +
                (op.deprecated ? "<span class=\"tag-deprecated\">deprecated</span>" : "") +
                "<button type=\"button\" class=\"pane-unpin\" data-unpin aria-label=\"Unpin " + escapeHtml(op.key) + "\" title=\"Unpin\">&times;</button>" +
            "</header>" +
            "<div class=\"pane-body\" id=\"" + bodyId + "\"><div class=\"swagger-host\"></div></div>";

        return { op: op, element: element, body: element.querySelector(".pane-body"), host: element.querySelector(".swagger-host"), ui: null, folded: false };
    };

    /* Fold or unfold a pane. Swagger UI is started the first time a pane is open, and kept after that, so a fold does not lose the request form. */
    Explorer.prototype.setFolded = function (key, folded) {
        var pane = this.panes[key];
        pane.folded = folded;
        pane.body.hidden = folded;
        pane.element.classList.toggle("is-folded", folded);
        pane.element.querySelector("[data-fold]").setAttribute("aria-expanded", folded ? "false" : "true");
        if (!folded && pane.ui === null) {
            this.startSwagger(pane);
        }
    };

    Explorer.prototype.startSwagger = function (pane) {
        if (typeof root.SwaggerUIBundle !== "function") {
            pane.host.innerHTML = "<p class=\"status status-error\" role=\"alert\">Swagger UI did not load, so this API cannot be shown.</p>";
            pane.ui = false;
            return;
        }

        var settings = {
            spec: Model.buildPaneDocument(this.document, pane.op),
            domNode: pane.host,
            presets: [root.SwaggerUIBundle.presets.apis],
            docExpansion: "full",
            deepLinking: false,
            defaultModelsExpandDepth: -1,
            defaultModelExpandDepth: 1,
            displayOperationId: false,
            tryItOutEnabled: this.config.tryItOutEnabled === true,
            validatorUrl: null
        };
        if (Array.isArray(this.config.supportedSubmitMethods)) {
            settings.supportedSubmitMethods = this.config.supportedSubmitMethods;
        }

        pane.ui = root.SwaggerUIBundle(settings);
    };

    /* ---- Start -------------------------------------------------------------------------------------------------------------------------- */

    function start(config) {
        var rootElement = root.document.getElementById("explorer");
        var explorer = new Explorer(rootElement, config);
        explorer.load();
        return explorer;
    }

    root.CCAIApiExplorer = { start: start, Explorer: Explorer };
}(typeof self !== "undefined" ? self : this));
