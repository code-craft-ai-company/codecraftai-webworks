.. _01-00-overview:

********
Overview
********

codecraftai-webworks is a Python web framework, ``ccai.webworks``, together with the browser-side libraries that
its applications use. This chapter describes how the pieces fit together. The next chapter,
:ref:`02-00-getting-started`, builds and serves an application.

How an application is put together
==================================

The web application persona
---------------------------
An application starts by *establishing its persona*. ``establish_webapp_persona`` creates the one
``WebApplication`` object of the process. It holds the application's name, the directory where it keeps its
settings and logs (its *presence directory*), its endpoint registry and, once started, its router, dispatcher and
ASGI application.

.. code-block:: python

    from ccai.webworks.webapplication import establish_webapp_persona

    webapp = establish_webapp_persona(
        name="hello",
        logger_name="hello",
        log_basename="hello",
        presence_dir=".presence",
    )

The persona is process-wide. Code that needs it later gets it from
``ccai.webworks.wellknown.ThisWebApplicationSingleton()``.

Endpoints
---------
An endpoint is a handler marked with a decorator. The decorator records where the handler should be served; it
does not register anything.

.. code-block:: python

    from ccai.webworks.endpoints.endpoint import Endpoint
    from ccai.webworks.routing.request import Request
    from ccai.webworks.routing.response import JSONResponse


    @Endpoint.attach_at(path="/health", methods=["GET"])
    def health(request: Request) -> JSONResponse:
        return JSONResponse(content={"status": "ok"}, status_code=200)

Related endpoints can be grouped in a ``Blueprint`` or ``RestBlueprint`` subclass, which gives them a common base
path, common tags and common access constraints.

Registration and startup
------------------------
The application says which endpoints are its own by collecting the modules, classes or functions that define
them, and then starts:

.. code-block:: python

    webapp.registry.collect_from(handlers)
    webapp.startup()

    app = webapp.asgi_app

``startup()`` runs the lifecycle phases in order: configuration, credentials, data profiles, database,
authentication and infrastructure. The infrastructure phase builds the router from the collected endpoints and
creates the ASGI application. ``webapp.asgi_app`` is that application; it is what a server serves.

Because registration is explicit, importing a module of handlers has no side effect, and an application serves
only the endpoints it collected.

Requests and responses
----------------------
The router matches the request path and method to an endpoint, the dispatcher calls the handler with a
``Request`` and turns the returned ``Response`` (``JSONResponse``, ``HTMLResponse``, ``RedirectResponse``,
``StreamingResponse`` or a plain ``Response``) into ASGI messages. Path parameters declared in the route, such as
``/items/{item_id}``, are available as ``request.path_params``.

The packages
============

================== ================================================================================================
Package            Purpose
================== ================================================================================================
``webapplication`` The ``WebApplication`` persona and ``establish_webapp_persona``
``asgi``           The ASGI application: HTTP, WebSocket, server-sent events, lifespan, error handling
``wsgi``           A WSGI layer: environ parsing, a socket server, ``wsgi_app`` (the WebApplication over WSGI)
``routing``        Router, dispatcher, ``Request``, the ``Response`` classes, multipart parsing, middleware
``endpoints``      ``Endpoint``, ``Blueprint``, ``RestBlueprint``, the endpoint registry, access policy and rate limit
``endpoints.rest`` REST endpoints: schemas, validation, serialization, content negotiation
``openapi``        OpenAPI generation, Swagger UI, ReDoc and the API explorer
``authentication`` Authenticators (basic, bearer, digest, HMAC, API key, session, OAuth 2, OpenID Connect)
``security``       Access policies, CSRF protection, signed serialization, JSON web tokens, password hashing
``templating``     Template engine interface with Jinja2 and Mako adapters
``configuration``  Layered configuration with schema validation
``markdown``       CommonMark renderer
``books``          Serves a folder of markdown books as HTML
``devexp``         Developer tools: the ``webworks`` command line, development server, test client, debug pages
``prodserver``     The production server (``webworks prodserve``): workers, limits, health, metrics, access log
``static``         The mj-* component library, the chart library and the design tokens
================== ================================================================================================

The browser-side libraries
==========================
The package ships its front-end assets in ``ccai/webworks/static``. They are plain ES modules and CSS; nothing is
compiled or bundled.

The mj-* component library
--------------------------
A library of native custom elements, one module per component in ``static/javascript/components``, built on the
shared foundation in ``static/javascript/core`` (the ``MjElement`` base class, registration, overlay positioning,
focus management, form association and internationalisation). A page loads the design tokens and the barrel
module, and then uses the elements:

.. code-block:: html

    <link rel="stylesheet" href="/static/styles/tokens.css">
    <script type="module" src="/static/javascript/index.js"></script>

    <mj-button variant="primary">Save</mj-button>

Every component takes its colours, spacing and typography from ``--mj-*`` design tokens, so a ``data-theme``
attribute on an ancestor re-themes everything beneath it.

The chart library
-----------------
``static/javascript/charts`` adds ``<mj-chart>``. Its ``type`` attribute selects a renderer and its data is JSON,
given through the ``data`` property, a ``src`` URL or an inline ``<script type="application/json">``. A chart's
title, legend and data table are separate elements bound to the chart by its id:

.. code-block:: html

    <script type="module" src="/static/javascript/charts/index.js"></script>

    <mj-chart id="sales" type="bar" src="/api/sales.json"></mj-chart>
    <mj-chart-legend chart="sales"></mj-chart-legend>

Serving the assets
------------------
The framework does not mount ``/static`` by itself. An application adds an endpoint that serves files from the
package's ``static`` directory. The testcomponents site does this in
``source/testsites/testcomponents/endpoints/handlers.py``, including the check that keeps a request from reaching
files outside that directory.

Where to see it working
=======================
``source/testsites`` contains three applications that are both test fixtures and examples:

- ``helloworld``: the smallest application.
- ``blueprintdemo``: REST blueprints with OpenAPI and Swagger UI.
- ``testcomponents``: a documentation and playground site for every component and chart type.

:ref:`02-00-getting-started` shows how to run them.
