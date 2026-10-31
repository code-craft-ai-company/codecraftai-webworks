# API explorer (tree and pinned panes)

`ccai.webworks.openapi.explorer` serves an interactive page for an OpenAPI document. It sits beside the Swagger UI page
(`ccai.webworks.openapi.swaggerui`), which lists every operation in one column; the explorer is for a document with hundreds of operations.

## Behaviour

- **Tree.** The left column is the document's operations grouped by where their paths live. A path parameter names no group; an action
  (`{id}:start`, `clients:inventory`) is a group `:start` under the item or collection it acts on. A group with one child group and no operations of its
  own folds into the child (`projects / rpa`). Each group shows how many operations it holds, each row shows the method, the summary and the part of the
  path the group's name does not already say.
- **Search.** Every space-separated term must match the row's path, summary, operation id or tags. A term that is a method name (`get`) matches that method
  only. A search opens every group that still has a match.
- **Pins.** A row is a toggle. A pinned operation opens in a pane on the right, in pin order. A pane has its own fold button, keeps its Try it out form
  while folded, and an unpin button. The toolbar folds, unfolds or unpins all.
- **Pane content.** Each pane starts Swagger UI on the document cut down to that one operation (the same `openapi`, `info`, `servers` and `security`, the
  path item's shared `parameters`, and only the components reached through `$ref`). Try it out, request bodies, responses and the examples are Swagger UI's, so
  a request goes where the Swagger UI page's would, as the signed-in person. Swagger UI's own title, server bar, group heading and summary row are hidden, since
  the pane's header already names the operation.
- **Address.** The fragment keeps the state: `#pin=GET+/projects&pin=POST+/projects&fold=GET+/projects&q=rpa`. A change to the pinned set is a step in the
  history (Back undoes it); folds and searches replace the current entry. A link that names an operation the document does not have still opens, with a notice.
- **Options.** `ExplorerOptions.supported_submit_methods` limits what Try it out may send (`None` all, `()` none, `("get",)` reads); `try_it_out_enabled`
  opens panes already in Try it out mode. The host decides the defaults.

## Decisions

- **Everything is built in the browser from the plain document.** The tree, the search and the pane documents need no endpoint beyond the document itself, so a
  host does not need `group_operations_by_path`. That function stays for hosts that want a tagged copy for Swagger UI.
- **The data model is a separate script with no page behind it** (`explorer-model.js`), so it runs under node in the unit tests.
- **Panes are not redrawn when the pinned set changes**, so a form someone has filled in survives pinning or unpinning another API.
- **The page is light.** Swagger UI's stylesheet is light only; the page matches it instead of putting a light widget on a dark page.
- **No script of its own, no other host.** The page, the starter script and the files are all served from one path, so the page works under a policy that
  allows scripts from its own origin only. The starter is a file because an inline one would be blocked.
- **Only named files are served.** `read_explorer_asset` hands out Swagger UI's three files and the explorer's three, and refuses every other name.

## Not done

- Pinning a whole group at once, reordering panes, and a dark theme.
