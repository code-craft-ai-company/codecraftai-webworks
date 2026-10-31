"""
.. module:: explorer
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: An API explorer page: a tree of an OpenAPI document's operations by path and a set of pinned panes, each running Swagger UI.

.. moduleauthor:: Code Craft AI LLC

The Swagger UI page (:mod:`ccai.webworks.openapi.swaggerui`) lists every operation in one long column. The explorer keeps Swagger UI's
**Try it out** and shows the document as a tree of where its paths live (``projects / rpa / specs``). A person ticks the few operations they
want and each opens as a pane of its own that folds by itself; the page address keeps the pinned set, so a link shares it.

A page made here needs three things from its host: the page, the starter script and the asset files, all served from one path, and the OpenAPI
document at a URL of its own. The page holds no inline script, so it works under a Content-Security-Policy that allows scripts from its own
origin only. Nothing is fetched from another host.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import html
import json

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from ccai.webworks.openapi.assets import AssetResolver
from ccai.webworks.openapi.swaggerui import SWAGGER_UI_ASSET_NAMES, read_swagger_ui_asset

#: The asset group (a directory of ``static/``) that holds the explorer's own files.
EXPLORER_ASSET_GROUP: str = "explorer"

#: The explorer's own files: the data model, the page script and the style sheet.
EXPLORER_OWN_ASSET_NAMES: Tuple[str, ...] = ("explorer-model.js", "explorer.js", "explorer.css")

#: Every file a page needs and the only ones :func:`read_explorer_asset` will hand out: Swagger UI's, then the explorer's.
EXPLORER_ASSET_NAMES: Tuple[str, ...] = SWAGGER_UI_ASSET_NAMES + EXPLORER_OWN_ASSET_NAMES

#: The name the starter script is served under next to the assets (see :func:`render_explorer_initializer`).
EXPLORER_INITIALIZER_NAME: str = "explorer-initializer.js"


@dataclass(frozen=True)
class ExplorerOptions:
    """
        How an explorer page behaves.

        :param supported_submit_methods: The HTTP methods Try it out may send (lower case). ``None`` allows every method; an empty tuple removes
                                         Try it out altogether; ``("get",)`` leaves reads only.
        :param try_it_out_enabled: Open each pane already in Try it out mode. Off, a person clicks **Try it out** and then **Execute**: two
                                   deliberate steps before a request is sent.
    """
    supported_submit_methods: Optional[Tuple[str, ...]] = None
    try_it_out_enabled: bool = False


def build_explorer_config(
        *,
        document_url: str,
        title: str,
        options: Optional[ExplorerOptions] = None
    ) -> Dict[str, Any]:
    """
        The configuration object the starter script passes to the page script.

        :param document_url: Where the page reads the OpenAPI document from (the plain document: the page builds its own tree).
        :param title: The API's name.
        :param options: The page's behaviour; the defaults of :class:`ExplorerOptions` when ``None``.

        :returns: The configuration as a JSON-serialisable dict.
    """
    chosen = options if options is not None else ExplorerOptions()

    rtnval: Dict[str, Any] = {
        "documentUrl": document_url,
        "title": title,
        "tryItOutEnabled": chosen.try_it_out_enabled,
    }
    if chosen.supported_submit_methods is not None:
        rtnval["supportedSubmitMethods"] = [method.lower() for method in chosen.supported_submit_methods]

    return rtnval


def render_explorer_initializer(
        *,
        document_url: str,
        title: str,
        options: Optional[ExplorerOptions] = None
    ) -> str:
    """
        The script that starts the explorer on a page made by :func:`render_explorer_page`. It is a file of its own, served beside the other
        assets, because a page whose Content-Security-Policy allows scripts from its own origin only cannot hold an inline starter.

        :param document_url: Where the page reads the OpenAPI document from.
        :param title: The API's name.
        :param options: The page's behaviour.

        :returns: JavaScript text.
    """
    config = build_explorer_config(document_url=document_url, title=title, options=options)
    config_text = json.dumps(config, indent=4, sort_keys=True).replace("\n", "\n    ")

    lines = [
        "(function () {",
        '    "use strict";',
        "    var config = {};".format(config_text),
        "    window.CCAIApiExplorer.start(config);",
        "}());",
        "",
    ]
    rtnval = "\n".join(lines)
    return rtnval


def render_explorer_page(
        *,
        title: str,
        static_path: str,
        initializer_name: str = EXPLORER_INITIALIZER_NAME
    ) -> str:
    """
        The explorer page: a container, the style sheets, and the scripts (Swagger UI, the explorer's model and page script, and the starter), all
        loaded from ``static_path``. The page holds no script of its own and names no other host.

        :param title: The page title (the API's name).
        :param static_path: The URL path the assets and the starter are served under (no trailing slash).
        :param initializer_name: The starter script's file name under ``static_path``.

        :returns: HTML text.
    """
    base = html.escape(static_path)

    lines = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '    <meta charset="UTF-8">',
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "    <title>{} - API explorer</title>".format(html.escape(title)),
        '    <link rel="stylesheet" href="{}/swagger-ui.css">'.format(base),
        '    <link rel="stylesheet" href="{}/explorer.css">'.format(base),
        '    <link rel="icon" type="image/png" href="{}/favicon-32x32.png" sizes="32x32">'.format(base),
        "</head>",
        "<body>",
        '    <div id="explorer"><noscript>The API explorer needs JavaScript.</noscript></div>',
        '    <script src="{}/swagger-ui-bundle.js"></script>'.format(base),
        '    <script src="{}/explorer-model.js"></script>'.format(base),
        '    <script src="{}/explorer.js"></script>'.format(base),
        '    <script src="{}/{}"></script>'.format(base, html.escape(initializer_name)),
        "</body>",
        "</html>",
        "",
    ]
    rtnval = "\n".join(lines)
    return rtnval


def read_explorer_asset(filename: str) -> Optional[Tuple[bytes, str]]:
    """
        One of the files an explorer page loads, by name. Only the names in :data:`EXPLORER_ASSET_NAMES` are served: any other name, including one
        that climbs out of the asset directory, is refused, so a route that serves these files never serves anything else.

        :param filename: The requested file name.

        :returns: ``(content, content type)``, or ``None`` when the name is not one of the explorer's files or the file is missing.
    """
    if filename in SWAGGER_UI_ASSET_NAMES:
        rtnval = read_swagger_ui_asset(filename)
        return rtnval

    if filename not in EXPLORER_OWN_ASSET_NAMES:
        return None

    resolver = AssetResolver()
    content = resolver.resolve(EXPLORER_ASSET_GROUP, filename)
    if content is None:
        return None

    rtnval = (content, resolver.content_type(filename))
    return rtnval


__all__ = [
    "EXPLORER_ASSET_GROUP",
    "EXPLORER_ASSET_NAMES",
    "EXPLORER_INITIALIZER_NAME",
    "EXPLORER_OWN_ASSET_NAMES",
    "ExplorerOptions",
    "build_explorer_config",
    "read_explorer_asset",
    "render_explorer_initializer",
    "render_explorer_page",
]
