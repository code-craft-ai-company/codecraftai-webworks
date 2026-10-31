/*
 * explorer_model_probe.js
 *
 * Runs the API explorer's data model (static/explorer/explorer-model.js) over a small document and prints what it produced as JSON, one member per
 * property under test. test_explorer_model.py runs this under node and checks each member; nothing here decides pass or fail.
 *
 *   node explorer_model_probe.js <path to explorer-model.js>
 */
"use strict";

var Model = require(process.argv[2]);

var DOCUMENT = {
    openapi: "3.1.0",
    info: { title: "Demo", version: "1" },
    servers: [{ url: "/api/v1" }],
    security: [{ session: [] }],
    tags: [{ name: "projects" }],
    paths: {
        "/": { get: { summary: "Index", responses: { "200": { description: "ok" } } } },
        "/projects": {
            get: { tags: ["projects"], summary: "List projects", operationId: "projects_list", responses: { "200": { $ref: "#/components/responses/Ok" } } },
            post: { tags: ["projects"], summary: "Create a project", requestBody: { content: { "application/json": { schema: { $ref: "#/components/schemas/ProjectNew" } } } }, responses: { "201": { description: "created" } } }
        },
        "/projects/{project_id}": {
            summary: "One project",
            parameters: [{ $ref: "#/components/parameters/ProjectId" }],
            get: { tags: ["projects"], summary: "Read a project", responses: { "200": { description: "ok" } } },
            delete: { tags: ["projects"], summary: "Delete a project", deprecated: true, responses: { "204": { description: "gone" } } },
            "x-internal": true
        },
        "/projects/{project_id}/rpa/specs": {
            get: { summary: "List specs", responses: { "200": { description: "ok" } } },
            post: { summary: "Create a spec", responses: { "201": { description: "created" } } }
        },
        "/projects/{project_id}/rpa/specs/{spec_id}:trigger": {
            post: { summary: "Trigger a spec", responses: { "202": { description: "accepted" } } }
        },
        "/projects/{project_id}/rpa/jobs/{job_id}": {
            get: { summary: "Read a job", responses: { "200": { description: "ok" } } }
        },
        "/clients": { get: { summary: "List clients", responses: { "200": { description: "ok" } } } },
        "/clients:inventory": { get: { summary: "Client inventory", responses: { "200": { description: "ok" } } } },
        "/settings/mail/templates": { get: { summary: "List mail templates", responses: { "200": { description: "ok" } } } },
        "/settings/mail/templates/{template_id}": { put: { summary: "Replace a mail template", responses: { "200": { description: "ok" } } } }
    },
    components: {
        schemas: {
            ProjectNew: { type: "object", properties: { owner: { $ref: "#/components/schemas/Owner" } } },
            Owner: { type: "object", properties: { name: { type: "string" } } },
            Unused: { type: "object" }
        },
        parameters: {
            ProjectId: { name: "project_id", in: "path", required: true, schema: { type: "string" } },
            UnusedParam: { name: "x", in: "query", schema: { type: "string" } }
        },
        responses: { Ok: { description: "ok", content: { "application/json": { schema: { $ref: "#/components/schemas/Owner" } } } } },
        securitySchemes: { session: { type: "apiKey", in: "cookie", name: "s" } }
    }
};

var before = JSON.stringify(DOCUMENT);
var operations = Model.buildOperations(DOCUMENT);
var byKey = Model.operationsByKey(operations);
var tree = Model.buildTree(operations);

function names(node) {
    return node.children.map(function (child) { return child.name; });
}

function childNamed(node, name) {
    return node.children.filter(function (child) { return child.name === name; })[0];
}

function outline(node) {
    return node.children.map(function (child) {
        return { name: child.name, depth: child.depth, count: child.count, ops: child.ops.map(function (op) { return op.key; }), children: outline(child) };
    });
}

var projects = childNamed(tree, "projects");
var rpa = childNamed(projects, "rpa");
var paneRead = Model.buildPaneDocument(DOCUMENT, byKey["GET /projects/{project_id}"]);
var paneCreate = Model.buildPaneDocument(DOCUMENT, byKey["POST /projects"]);
var paneJob = Model.buildPaneDocument(DOCUMENT, byKey["GET /projects/{project_id}/rpa/jobs/{job_id}"]);

function terms(text) {
    return Model.parseQuery(text);
}

function matching(text) {
    return operations.filter(function (op) { return Model.matches(op, terms(text)); }).map(function (op) { return op.key; });
}

var hashState = { pins: ["GET /projects", "POST /projects/{project_id}/rpa/specs/{spec_id}:trigger", "GET /projects"], folds: ["GET /projects", "GET /elsewhere"], query: "mail templates" };
var hashText = Model.buildHash(hashState);

var results = {
    splitPath: {
        plain: Model.splitPath("/projects/{project_id}/rpa/specs"),
        itemAction: Model.splitPath("/projects/{project_id}/rpa/specs/{spec_id}:trigger"),
        collectionAction: Model.splitPath("/clients:inventory"),
        root: Model.splitPath("/"),
        onlyParameter: Model.splitPath("/{thing_id}")
    },
    operationKeys: operations.map(function (op) { return op.key; }),
    operationMembers: {
        notOperations: operations.filter(function (op) { return ["parameters", "summary", "x-internal"].indexOf(op.method.toLowerCase()) >= 0; }).length,
        deprecated: byKey["DELETE /projects/{project_id}"].deprecated,
        notDeprecated: byKey["GET /projects"].deprecated,
        tags: byKey["GET /projects"].tags,
        operationIdWhenAbsent: byKey["GET /"].operationId
    },
    topLevel: names(tree),
    outline: outline(tree),
    folded: {
        name: childNamed(tree, "settings / mail / templates").name,
        id: childNamed(tree, "settings / mail / templates").id,
        depth: childNamed(tree, "settings / mail / templates").depth,
        ops: childNamed(tree, "settings / mail / templates").ops.length
    },
    projectsRpaKids: names(rpa),
    restOf: {
        itemInGroup: Model.restOf(byKey["GET /projects/{project_id}"], projects),
        collectionInGroup: Model.restOf(byKey["GET /projects"], projects),
        jobInGroup: Model.restOf(byKey["GET /projects/{project_id}/rpa/jobs/{job_id}"], childNamed(rpa, "jobs")),
        specsInGroup: Model.restOf(byKey["GET /projects/{project_id}/rpa/specs"], childNamed(rpa, "specs")),
        actionInGroup: Model.restOf(byKey["POST /projects/{project_id}/rpa/specs/{spec_id}:trigger"], childNamed(childNamed(rpa, "specs"), ":trigger")),
        collectionInClients: Model.restOf(byKey["GET /clients"], childNamed(tree, "clients")),
        collectionActionInGroup: Model.restOf(byKey["GET /clients:inventory"], childNamed(childNamed(tree, "clients"), ":inventory"))
    },
    groupIds: {
        trigger: Model.groupIdsFor(tree, "POST /projects/{project_id}/rpa/specs/{spec_id}:trigger"),
        projectsList: Model.groupIdsFor(tree, "GET /projects"),
        unknown: Model.groupIdsFor(tree, "GET /nowhere")
    },
    query: {
        terms: terms("  Mail   TEMPLATES "),
        empty: terms("   "),
        everyTerm: matching("mail replace"),
        byMethod: matching("delete"),
        methodAndWord: matching("post spec"),
        word: matching("inventory"),
        summaryWord: matching("trigger"),
        tagWord: matching("projects").length,
        none: matching("zzz"),
        methodNameIsNotASubstring: matching("get").filter(function (key) { return key.indexOf("GET ") !== 0; })
    },
    pruned: (function () {
        var pruned = Model.pruneTree(tree, function (op) { return op.method === "DELETE"; });
        return { names: names(pruned), count: pruned.count, kept: outline(pruned), fullCountUnchanged: tree.count };
    }()),
    address: {
        text: hashText,
        parsed: Model.parseHash("#" + hashText),
        parsedWithoutHash: Model.parseHash(hashText),
        empty: Model.parseHash(""),
        emptyText: Model.buildHash({ pins: [], folds: [], query: "" }),
        readable: hashText.indexOf("%2F") < 0 && hashText.indexOf("%7B") < 0
    },
    paneRead: paneRead,
    paneCreate: paneCreate,
    paneJob: paneJob,
    inputUnchanged: JSON.stringify(DOCUMENT) === before,
    reachable: Model.reachableComponents(DOCUMENT.components, [{ $ref: "#/components/responses/Ok" }, { $ref: "#/components/schemas/Missing" }, { $ref: "#/paths/~1projects" }])
};

process.stdout.write(JSON.stringify(results));
