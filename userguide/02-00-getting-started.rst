.. _02-00-getting-started:

***************
Getting Started
***************

This chapter creates an application, serves it, adds an endpoint and tests it. Every command is run from a shell
in which the package is installed (see `Installing`_).

Installing
==========
The package needs Python 3.10 or later. With the Code Craft AI package repository configured as a package source:

.. code-block:: bash

    pip install codecraftai-webworks

Installing the package provides the ``webworks`` command. Where the command is not on the path, every example
below also works with ``python -m ccai.webworks.devexp.cli`` in place of ``webworks``.

Optional features are extras, installed as ``codecraftai-webworks[name]``: ``jinja2``, ``mako`` and ``templating``
(template engines), ``pydantic`` (Pydantic models as REST schemas), ``gevent`` (the gevent production worker),
``toml`` (TOML configuration files), ``shell`` (IPython for ``webworks shell``) and ``test`` (the testbase runner
and Playwright).

Working on the framework itself uses the repository's own environment instead:

.. code-block:: bash

    python repository-setup/rehome-repository
    python development/setup-environment
    poetry install --extras "templating test"
    source .venv/bin/activate

Creating a project
==================

.. code-block:: bash

    webworks new my-project
    cd my-project

``webworks new`` writes a small, working application:

.. code-block:: text

    my-project/
      app.py                 establishes the persona and exposes the ASGI application as 'app'
      config.py              the application name, presence directory, host and port
      endpoints/
        handlers.py          the endpoint handlers

The ``--template`` option chooses how much is generated:

- ``minimal`` (the default): one endpoint at ``/``.
- ``api``: adds ``/api/health``, a ``RestBlueprint`` under ``/api/items`` (``blueprints/items.py``), a model
  (``models/item.py``) and tests (``tests/test_app.py``).
- ``webapp``: everything in ``api``, plus an HTML page rendered from ``templates/index.html`` and assets served
  from ``static/``.

The generated ``app.py`` follows the pattern described in :ref:`01-00-overview`: establish the persona, collect
the endpoint modules, start, and expose ``app``.

Serving it
==========

.. code-block:: bash

    webworks serve --reload

The server listens on ``http://127.0.0.1:8000``. In another shell:

.. code-block:: bash

    curl http://127.0.0.1:8000/

``webworks serve`` needs to know which application to serve. It looks, in this order, at:

1. the ``--app`` option, an import target of the form ``module:attribute``, for example ``--app app:app`` or
   ``--app mysite.app:app``;
2. the ``server.app`` configuration key (``WEBWORKS_SERVER_APP`` in the environment);
3. ``app:app``, when the current directory contains ``app.py``.

The command exits with an error when it finds no application or cannot import it.

Options of ``webworks serve``:

==================== =================================================================================
Option               Meaning
==================== =================================================================================
``--app TARGET``     The application, as ``module:attribute``
``--host HOST``      Address to bind to. Default ``127.0.0.1``
``--port PORT``      Port to bind to. Default ``8000``
``--reload``         Restart the server when a source file changes
``--extra-files``    More file patterns to watch with ``--reload``, comma separated: ``'*.html,*.css'``
``--debug``          Turn debug mode on explicitly
``--no-debug``       Turn debug mode off
``--log-level``      ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR`` or ``CRITICAL``
``--log-file FILE``  Also write the log to a file
==================== =================================================================================

Reloading
---------
With ``--reload`` the command does not serve requests itself. It starts the server as a child process and watches
the source files (``**/*.py`` plus anything named by ``--extra-files``) under the current directory. When a file
changes, the child process is stopped and a new one is started, which imports the application from scratch. If the
edited file has an error, the error is printed and the command keeps watching; the server comes back at the next
save.

Debug mode
----------
In debug mode an unhandled error is answered with the exception and its traceback. That is useful on your own
machine and unsafe anywhere else, so:

- debug mode follows the ``server.debug`` configuration key, which is on by default;
- ``--no-debug`` turns it off;
- when the server binds to an address that other machines can reach (for example ``--host 0.0.0.0``), debug mode is
  turned off and a warning is printed, unless ``--debug`` is given explicitly.

Request IDs
-----------
Every request gets an ID. It prefixes the log lines written while the request is handled and is returned in the
``X-Request-ID`` response header. A request that arrives with an ``X-Request-ID`` header keeps that ID.

Serving in production
=====================
``webworks serve`` is the development server. In production the application is served by the production server,
or by any WSGI or ASGI server:

.. code-block:: bash

    webworks prodserve --app mysite.app:webapp --host 0.0.0.0 --port 8000 --workers 4

``webworks prodserve`` finds the application the way ``webworks serve`` does (``--app``, then ``server.app``, then
``./app.py``); the target may name the ``WebApplication`` or the ``app`` the module exports. It binds the port, starts
the worker processes (``--workers``, default 2 x CPU cores + 1, each with ``--threads`` threads) and serves until it
receives SIGTERM or SIGINT, which let the requests in flight finish (``--graceful-timeout``). SIGHUP replaces the
workers without dropping connections. The exit code is 0 after a clean shutdown and non-zero when the port is taken,
the PID file belongs to a running server, or the application cannot be loaded.

What the production server adds on every request:

- an ``X-Request-ID`` (the client's, when it is a short token, otherwise a generated one), passed to the handler in
  the request headers and returned in the response;
- a structured access log line (``--log-format json``, ``--access-log FILE``) with the request ID and the worker;
- ``GET /health`` (``--health-check-path``): 200 with a JSON status, 503 while a worker stops or when the
  application's startup handlers failed;
- ``GET /metrics`` (``--metrics-path``): Prometheus metrics of all workers together;
- limits: ``--limit-request-body`` (413, 16 MiB by default), ``--limit-request-line`` (414),
  ``--limit-request-fields`` and ``--limit-request-field-size`` (431), ``--timeout`` (504 when a handler does not
  answer in time), ``--max-requests`` (a worker is replaced after that many requests), ``--limit-memory``;
- ``--ssl-certfile``/``--ssl-keyfile`` for HTTPS, ``--ssl-redirect`` to redirect plain HTTP (also behind a proxy
  that sets ``X-Forwarded-Proto``);
- ``--pid-file``, ``--user``/``--group`` (dropped after the port is bound), ``--daemon``, ``--chdir``, ``--preload``.

Every option is also a key of the ``prodserver`` configuration section: ``{"prodserver": {"workers": 4}}`` in the
configuration file, or ``WEBWORKS_PRODSERVER_WORKERS=4`` in the environment. ``webworks prodserve --help`` lists
them all. The gevent worker class (``--worker-class gevent``) needs the ``gevent`` extra.

Other servers
-------------
``webapp.asgi_app`` is an ASGI 3 application; serve it with any ASGI server. ``webapp.wsgi_app`` is a WSGI (PEP 3333)
application that runs the same ASGI pipeline, so routes, authentication, limits, error handling and the startup and
shutdown handlers behave the same. For a WSGI server that loads a callable by name:

.. code-block:: bash

    WEBWORKS_SERVER_APP=mysite.app:webapp gunicorn 'ccai.webworks.wsgi.application:get_wsgi_application()'

``get_wsgi_application()`` serves the application named by ``WEBWORKS_SERVER_APP``, or the web application persona
the process established; ``ccai.webworks.wsgi.application:application`` is the same callable for servers that load a
module attribute. WebSocket routes need an ASGI server.

Looking at the routes
=====================

.. code-block:: bash

    webworks routes
    webworks routes --format json
    webworks routes --filter "/api/*" --verbose

``webworks routes`` imports the application and lists every route of its router: path, methods, handler and
whether the endpoint requires authentication. ``--format`` is ``table``, ``json`` or ``csv``; ``--filter`` is a
glob pattern matched against the path.

Adding an endpoint
==================
Generate an endpoint module:

.. code-block:: bash

    webworks generate endpoint user-profile --output-dir endpoints

This writes ``endpoints/user_profile.py`` with a handler attached at ``/user-profile``. The name is converted to
snake_case and must be a valid Python identifier. A generated handler is only marked; the application has to
collect it. In ``app.py``:

.. code-block:: python

    from endpoints import handlers
    from endpoints import user_profile

    webapp.registry.collect_from(handlers, user_profile)

``webworks routes`` now lists ``/user-profile``. ``webworks generate blueprint NAME`` writes a ``RestBlueprint``
subclass in the same way, and ``--dry-run`` prints either file instead of writing it.

An endpoint is an ordinary function:

.. code-block:: python

    from ccai.webworks.endpoints.endpoint import Endpoint
    from ccai.webworks.routing.request import Request
    from ccai.webworks.routing.response import JSONResponse


    @Endpoint.attach_at(path="/items/{item_id}", methods=["GET"])
    def get_item(request: Request) -> JSONResponse:
        item_id = request.path_params.get("item_id")
        return JSONResponse(content={"item_id": item_id}, status_code=200)

Testing an endpoint
===================
``TestClient`` calls the application in-process, with a real ASGI request, so routing and middleware run as they
do under a server:

.. code-block:: python

    from ccai.webworks.devexp.testing.testclient import TestClient

    import app as application


    def test_health_reports_ok():
        client = TestClient(application.app)

        response = client.get("/api/health")

        assert response.status_code == 200
        assert response.json == {"status": "ok"}

The client keeps cookies between requests the way a browser does: a cookie's ``Path``, ``Domain`` and ``Secure``
attributes decide which requests it is sent with, and a cookie the server expires is removed. Beyond ``get``,
``post``, ``put``, ``patch``, ``delete``, ``head`` and ``options`` it offers:

- ``json=``, ``data=`` (form fields), ``content=`` (raw bytes) and ``files=`` (multipart upload) for the body;
- ``params=`` for the query string and ``headers=`` for request headers;
- ``follow_redirects=True`` to follow redirects, with the intermediate responses in ``response.history``;
- ``response.get_headers("Set-Cookie")`` for headers that occur more than once;
- ``with TestClient(app) as client:`` to run the application's lifespan startup and shutdown around the tests.

The client also accepts a WSGI application, and a plain function with the signature
``(method, path, headers, body) -> (status_code, headers, body)``.

An interactive shell
====================

.. code-block:: bash

    webworks shell

opens a Python shell with the application loaded: ``app`` is the ASGI application, ``webapp`` the persona, and
``router`` and ``registry`` its router and endpoint registry. IPython is used when it is installed
(``--no-ipython`` forces the standard shell). A file named ``.webworks_shell.py`` in the current directory is run
first, so it can import whatever you usually need.

Database commands
=================
``WebApplication`` has four database hooks that an application overrides: ``prepare_database``,
``connect_database``, ``startup_database`` and ``ensure_database_ready``.

.. code-block:: bash

    webworks db init
    webworks --env staging db init

``webworks db init`` runs those hooks in order and fails if ``ensure_database_ready`` does not return ``True``.

``webworks db migrate``, ``rollback``, ``seed`` and ``status`` need more than the hooks provide. They work when the
application supplies a ``DatabaseBackend`` (``ccai.webworks.devexp.cli.database.DatabaseBackend``) as a
``database_backend`` attribute of the application module or of the persona, or when the ``WebApplication`` subclass
defines ``get_pending_migrations``, ``get_applied_migrations``, ``apply_migration``, ``rollback_migration`` and
``seed_database``. Without either they report what is missing and exit with an error.

Configuration
=============
The command line reads its settings from three places. Later ones win:

1. built-in defaults;
2. a JSON file named with the global ``--config`` option;
3. environment variables named ``WEBWORKS_<SECTION>_<KEY>``.

.. code-block:: json

    {
        "server": {"app": "app:app", "host": "127.0.0.1", "port": 8123, "debug": true, "reload": false},
        "logging": {"level": "INFO"}
    }

.. code-block:: bash

    webworks --config dev.json serve
    WEBWORKS_SERVER_PORT=9000 webworks serve

A configuration file that is named but missing, unreadable or not a JSON object stops the command with an error;
it is never silently replaced by the defaults.

The global options ``--config``, ``--app``, ``--env`` and ``--verbose`` are written before the command name.
``--verbose`` prints the traceback when a command fails.

Running the sample sites
========================
From a checkout of the repository, with its environment active:

.. code-block:: bash

    PYTHONPATH=source/testsites webworks serve --app helloworld.app:app
    PYTHONPATH=source/testsites webworks serve --app blueprintdemo.app:app
    PYTHONPATH=source/testsites webworks serve --app testcomponents.app:app

``helloworld`` answers at ``/`` and ``/health``. ``blueprintdemo`` has Swagger UI at ``/docs``. ``testcomponents``
is the documentation and playground site for the component and chart libraries: its landing page lists the
components by group and ``/charts`` lists the chart types.

Running the tests
=================
The framework's own tests run under the ``testbase`` runner:

.. code-block:: bash

    testbase testing run --root source/testroots/ccai --includes=ccai.tests.singlehost --output=./.output/

The browser suite of the testcomponents site needs Playwright (part of the ``test`` extra) and its Chromium
browser. Without them every test in the suite is reported as skipped:

.. code-block:: bash

    python -m playwright install chromium
    testbase testing run --root ./source/testsites/testcomponents --includes=testcomponents.tests --output=./.output/testcomponents-tests
