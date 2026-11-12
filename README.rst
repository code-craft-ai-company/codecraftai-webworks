====================
codecraftai-webworks
====================

Code Craft AI - WebWorks

Overview
========
codecraftai-webworks is the web framework of the Code Craft AI technology stack. It is a Python package
(``ccai.webworks``) for building web applications and REST APIs, and it ships the browser-side pieces that go with
them: a library of ``mj-*`` web components, a chart library and an API explorer, all served as static assets with no
build step.

An application is built around a *web application persona*: one object that owns the application's identity, its
configuration, its endpoint registry, its router and its ASGI application. Endpoints are plain functions or classes
marked with a decorator; the application declares which ones belong to it and the framework builds the router from
them.

What is in the package
======================

Server side (``ccai.webworks``):

- **ASGI and WSGI layers** (``asgi``, ``wsgi``): an ASGI 3.0 application with HTTP, WebSocket, server-sent event and
  lifespan handling, and a WSGI layer with request parsing, response building, a socket server and the bridge that
  serves a ``WebApplication`` over WSGI.
- **Routing** (``routing``): a URL-node router with path parameters and converters, a dispatcher, request and
  response classes (JSON, HTML, redirect, streaming), multipart parsing and a middleware pipeline.
- **Endpoints and blueprints** (``endpoints``): ``Endpoint.attach_at`` for single handlers; ``Blueprint`` and
  ``RestBlueprint`` for groups of handlers under a base path; access policies and rate limits declared on the
  endpoint.
- **REST and OpenAPI** (``endpoints.rest``, ``openapi``): request and response schemas, content negotiation, an
  OpenAPI generator, Swagger UI, ReDoc and the bundled API explorer. A route that declares a request schema,
  response schema or error map is REST-processed automatically (validation, negotiation, serialization, REST error
  bodies); pass ``rest_processing=False`` when registering it to handle the raw request yourself.
- **Authentication and security** (``authentication``, ``security``): basic, bearer, digest, HMAC, API key, session,
  OAuth 2 and OpenID Connect authenticators; access policies, CSRF protection, signed serialization, JSON web
  tokens and password hashing.
- **Templating** (``templating``): a pluggable template engine interface with Jinja2 and Mako adapters, context
  processors, filters and auto-escaping.
- **Configuration** (``configuration``): layered configuration from files, the environment and defaults, with
  schema validation.
- **Extensions** (``extensibility``): add extensions in code with ``webapp.add_extension(...)`` or list them in the
  ``extensions`` configuration section (``load``, ``entry_points``, ``paths``, with an ``allowed_packages``
  allow-list); they get application and request lifecycle hooks and can contribute middleware. Nothing is imported
  unless it is configured.
- **Markdown books** (``markdown``, ``books``): a CommonMark renderer with no third-party dependency, and a
  blueprint that serves a folder of markdown books as navigable HTML (see `Markdown Books`_).
- **Developer tools** (``devexp``): the ``webworks`` command line, a development server with auto-reload, an
  in-process test client, debug error pages and request inspection (see `The webworks command line`_).
- **Production server** (``prodserver``): ``webworks prodserve`` runs an application on pre-forked worker processes
  with graceful shutdown and reload, request IDs, health and metrics endpoints, a structured access log, request
  limits and TLS. A ``WebApplication`` is also served by any WSGI server through ``webapp.wsgi_app``.

Browser side (``ccai/webworks/static``, shipped inside the package):

- **The mj-* component library**: native custom elements (see `The mj-* component library`_).
- **The chart library**: ``<mj-chart>`` and its renderers (see `The chart library`_).

Installation
============
The package requires Python 3.10 or later. Releases are built by the ``Publish`` workflow and uploaded to the Code
Craft AI package repository (and to PyPI when the organization enables it). With that repository configured as a
package source:

.. code-block:: bash

    pip install codecraftai-webworks

Optional features are installed as extras:

=============== ==================================================================================
Extra           Installs
=============== ==================================================================================
``jinja2``      Jinja2, for the Jinja2 template adapter
``mako``        Mako, for the Mako template adapter
``templating``  both template engines
``pydantic``    Pydantic 2, for Pydantic models as REST schemas and in the OpenAPI schema converter
``gevent``      gevent, for the gevent worker of the production server
``toml``        tomli (Python 3.10) and tomli-w, for TOML configuration files
``shell``       IPython, used by ``webworks shell`` when it is installed
``test``        the testbase runner and Playwright, for running the test suites
=============== ==================================================================================

.. code-block:: bash

    pip install "codecraftai-webworks[jinja2,pydantic]"

A minimal application
=====================
Save this as ``app.py``:

.. code-block:: python

    from ccai.webworks.endpoints.endpoint import Endpoint
    from ccai.webworks.routing.request import Request
    from ccai.webworks.routing.response import JSONResponse
    from ccai.webworks.webapplication import establish_webapp_persona


    @Endpoint.attach_at(path="/", methods=["GET"])
    def index(request: Request) -> JSONResponse:
        return JSONResponse(content={"message": "Hello, World!"}, status_code=200)


    webapp = establish_webapp_persona(
        name="hello",
        logger_name="hello",
        log_basename="hello",
        presence_dir=".presence",
    )

    # The decorator only marks the handler; collecting it registers the route.
    webapp.registry.collect_from(index)
    webapp.startup()

    # The ASGI application: serve it with 'webworks serve' or any ASGI server.
    app = webapp.asgi_app

Serve it from the same directory and request it:

.. code-block:: bash

    webworks serve --reload
    curl http://127.0.0.1:8000/

``webworks serve`` looks for ``app:app`` in the current directory; name another application with
``--app module:attribute``. With ``--reload`` the server runs in a child process that is replaced whenever a source
file changes, so the edited code is imported afresh.

The same application can be called in a test without a server:

.. code-block:: python

    from ccai.webworks.devexp.testing.testclient import TestClient

    from app import app

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert response.json == {"message": "Hello, World!"}

The webworks command line
=========================
Installing the package adds the ``webworks`` command. It can also be run as ``python -m ccai.webworks.devexp.cli``.

===================================== ==============================================================================
Command                               Does
===================================== ==============================================================================
``webworks new NAME``                 Create a project. ``--template minimal`` (default), ``api`` or ``webapp``.
``webworks serve``                    Run the development server. ``--app``, ``--host``, ``--port``, ``--reload``,
                                      ``--debug``, ``--no-debug``, ``--extra-files``, ``--log-level``, ``--log-file``.
``webworks routes``                   List the application's routes. ``--format table|json|csv``, ``--filter``,
                                      ``--verbose``.
``webworks shell``                    Open a Python shell with ``app``, ``webapp``, ``router`` and ``registry``
                                      loaded.
``webworks generate endpoint NAME``   Write an endpoint module. ``--output-dir``, ``--dry-run``.
``webworks generate blueprint NAME``  Write a ``RestBlueprint`` module. ``--output-dir``, ``--dry-run``.
``webworks db init``                  Run the persona's database hooks. ``migrate``, ``rollback``, ``seed`` and
                                      ``status`` need a database backend provided by the application.
===================================== ==============================================================================

The global options ``--app``, ``--config FILE`` (a JSON file), ``--env`` and ``--verbose`` go before the command
name. Settings can also come from the environment: ``WEBWORKS_SERVER_PORT=9000`` sets ``server.port``. The user
guide's `Getting Started <userguide/02-00-getting-started.rst>`_ chapter walks through all of this.

The development server is for development. In debug mode an unhandled error is answered with its traceback, so
debug mode is switched off when the server binds to an address other machines can reach, unless ``--debug`` is
given explicitly.

The mj-* component library
==========================
``ccai/webworks/static`` holds a framework-agnostic library of native custom elements in eleven groups: buttons,
selection, text, data, navigation, overlays, layout, feedback, media, productivity and charts. Each component is one ES module under ``static/javascript/components`` (``mj<name>.js``)
built on a small shared foundation in ``static/javascript/core``. There is no build step and no runtime dependency.

.. code-block:: html

    <!-- Design tokens: link once at the document level. -->
    <link rel="stylesheet" href="/static/styles/tokens.css">

    <!-- All components, registered automatically. -->
    <script type="module" src="/static/javascript/index.js"></script>

    <mj-button variant="primary">Save</mj-button>

Components are styled only through ``--mj-*`` design tokens (``static/styles/tokens.css``), with light, dark and
high-contrast themes selected by a ``data-theme`` attribute on any ancestor. An application serves the directory
itself; the testcomponents site shows how in ``source/testsites/testcomponents/endpoints/handlers.py``. The
library's own documentation is ``source/packages/ccai/webworks/static/javascript/README.md`` and a live demo of
components, docking, anchoring and theming is ``static/gallery.html``.

The chart library
=================
``static/javascript/charts`` is a chart library built on the same foundation. A chart is an ``<mj-chart>`` element
whose ``type`` selects a renderer (``bar``, ``line``, ``pie``, ``scatter``, ``heatmap``, ``sankey`` and
many more; each renderer is a module under ``charts/core/renderers``) and whose data is JSON given through the ``data`` property, a ``src`` URL
or an inline ``<script type="application/json">``. The title, legend and data table of a chart are separate
elements (``<mj-chart-title>``, ``<mj-chart-legend>``, ``<mj-chart-data-table>``) that bind to the chart by its id
and can be placed independently.

.. code-block:: html

    <script type="module" src="/static/javascript/charts/index.js"></script>

    <mj-chart id="sales" type="bar" src="/api/sales.json"></mj-chart>
    <mj-chart-legend chart="sales"></mj-chart-legend>

The exact attributes and the data shape of every chart type are documented, with live examples, by the
testcomponents site.

The test sites
==============
``source/testsites`` holds three sample applications. They are fixtures for the test suites and working examples
of the framework:

- **helloworld**: the smallest application; two endpoints.
- **blueprintdemo**: ``RestBlueprint`` inheritance with OpenAPI and Swagger UI at ``/docs``.
- **testcomponents**: documents and exercises the component and chart libraries. It has a browse-by-group landing
  page, a page per component with attribute and event tables and a live, editable playground, and a ``/charts``
  section with a page per chart type. It needs no authentication.

Run one from the repository root:

.. code-block:: bash

    PYTHONPATH=source/testsites webworks serve --app testcomponents.app:app

Markdown Books
==============
``BooksBlueprint`` serves a folder of markdown books as HTML pages. Navigation comes from the links in the markdown,
not from the folders the files are in: the library's index document (``README.md`` at the root) links to the books,
each book's index document links to its chapters, and the order of those links, in lists or tables, is the reading
order. The text of each link is the title the navigation shows. A link to a folder means the folder's ``README.md``
(or ``index.md``).

.. code-block:: python

    from ccai.webworks.books import BookLibrary, BooksBlueprint

    library = BookLibrary("~/repos/codecraftai-books")
    books = BooksBlueprint(library, mount_path="/books")
    books.attach_to_webapp(webapp)

Each page shows its book's contents, breadcrumbs, links to the previous and next documents and an outline of its
headings. Links between the markdown files are rewritten to the URLs the documents are served at, and images in the
library are served beside them. Nothing outside the library's folder, and no hidden file, is ever served. Pages carry
a Content-Security-Policy that allows no script.

The markdown is rendered by ``ccai.webworks.markdown`` (no third-party library): CommonMark plus GitHub tables,
strikethrough and links made from bare addresses. Raw HTML in the markdown is escaped and links with unsafe schemes
such as ``javascript:`` are dropped.

To read a library with the development server:

.. code-block:: bash

    python source/examples/books/serve_books.py ~/repos/codecraftai-books --port 8000

Development
===========
The repository uses Poetry for its environment.

1. Prepare the checkout and create the virtual environment in ``.venv``:

   .. code-block:: bash

       python repository-setup/rehome-repository
       python development/setup-environment
       poetry install --extras "templating test"
       source .venv/bin/activate

2. Run the single-host suite. Tests run under the ``testbase`` runner:

   .. code-block:: bash

       testbase testing run --root source/testroots/ccai --includes=ccai.tests.singlehost --output=./.output/

3. Run the browser suite of the testcomponents site. It drives the component and chart libraries in Chromium
   through Playwright (installed by the ``test`` extra); download the browser once first. Without Playwright or its
   browser every test in this suite is reported as skipped, not passed:

   .. code-block:: bash

       python -m playwright install chromium
       testbase testing run --root ./source/testsites/testcomponents --includes=testcomponents.tests --output=./.output/testcomponents-tests

The ``Merge Gate`` workflow runs both suites, builds the wheel and smoke-tests it; the ``Publish`` workflow uploads
a release only after that gate has passed. ``make test``, ``make test-components`` and ``make dist-build`` run the
same steps locally.

References
==========
- `User Guide <userguide/userguide.rst>`_
- `Getting Started <userguide/02-00-getting-started.rst>`_
- `Coding Standards <userguide/10-00-coding-standards.rst>`_
- `Component library <source/packages/ccai/webworks/static/javascript/README.md>`_
- `testcomponents site <source/testsites/testcomponents/README.md>`_
