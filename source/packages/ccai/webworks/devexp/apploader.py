"""
    Application loading for the webworks developer tools.

    This module resolves an application from an import target of the form
    ``module:attribute`` (for example ``app:app`` or
    ``mysite.app:application``). The command line (``serve``, ``routes``,
    ``shell`` and ``db``) and the development server both use it, so the
    target is interpreted the same way everywhere.

    The target is found, in order, from:

    1. the ``--app`` command-line option,
    2. the ``server.app`` configuration key (``WEBWORKS_SERVER_APP`` in the
       environment),
    3. ``app:app`` when the current directory contains an ``app.py`` file,
       which is the layout ``webworks new`` generates.
"""

import importlib
import os
import sys

from typing import Any, Dict, Optional, Tuple


DEFAULT_APP_MODULE = "app"
"""Module name looked for in the current directory when no target is given."""

DEFAULT_APP_ATTRIBUTE = "app"
"""Attribute name used when a target names only a module."""

TARGET_SEPARATOR = ":"
"""Separator between the module path and the attribute path of a target."""


class ApplicationLoadError(Exception):
    """
        Raised when an application import target cannot be resolved.

        The message is written for the person at the command line: it names
        the target and says which part of it could not be resolved.
    """


def parse_app_target(target: str) -> Tuple[str, str]:
    """
        Split an import target into its module path and attribute path.

        A target without a separator names a module; the attribute then
        defaults to ``app``.

        :param target: The import target, ``module`` or ``module:attribute``.

        :returns: A tuple of (module_path, attribute_path).

        :raises ApplicationLoadError: If the target is empty or malformed.
    """
    if not isinstance(target, str) or len(target.strip()) == 0:
        errmsg = "The application target is empty. Expected 'module:attribute', for example 'app:app'."
        raise ApplicationLoadError(errmsg)

    cleaned = target.strip()

    if TARGET_SEPARATOR in cleaned:
        module_path, attribute_path = cleaned.split(TARGET_SEPARATOR, 1)
    else:
        module_path = cleaned
        attribute_path = DEFAULT_APP_ATTRIBUTE

    module_path = module_path.strip()
    attribute_path = attribute_path.strip()

    module_parts = module_path.split(".")
    attribute_parts = attribute_path.split(".")

    for part in module_parts + attribute_parts:
        if not part.isidentifier():
            errmsg = "The application target '{}' is not valid. Expected 'module:attribute', for example 'app:app'.".format(
                target
            )
            raise ApplicationLoadError(errmsg)

    return module_path, attribute_path


def resolve_app_target(args: Any, config: Dict[str, Any]) -> Optional[str]:
    """
        Determine the application import target for a command.

        The ``--app`` option takes precedence over the ``server.app``
        configuration key. When neither is given and the current directory
        contains ``app.py``, the target is ``app:app``.

        :param args: Parsed command-line arguments, or ``None``.
        :param config: Loaded configuration dictionary.

        :returns: The import target, or ``None`` when none can be determined.
    """
    target = getattr(args, "app", None)

    if target is None:
        server_config = config.get("server", {})
        if isinstance(server_config, dict):
            target = server_config.get("app", None)

    if target is None:
        candidate = os.path.join(os.getcwd(), DEFAULT_APP_MODULE + ".py")
        if os.path.isfile(candidate):
            target = DEFAULT_APP_MODULE + TARGET_SEPARATOR + DEFAULT_APP_ATTRIBUTE

    if target is not None and not isinstance(target, str):
        target = None

    return target


def ensure_import_path(directory: Optional[str] = None) -> None:
    """
        Make sure a directory is importable, so ``app:app`` finds ``./app.py``.

        A console script does not put the current directory on ``sys.path``
        the way ``python script.py`` does, so the loader adds it.

        :param directory: The directory to add. Defaults to the current
            working directory.
    """
    if directory is None:
        directory = os.getcwd()

    if directory not in sys.path:
        sys.path.insert(0, directory)

    return


def load_application(target: str) -> Any:
    """
        Import an application from a ``module:attribute`` target.

        :param target: The import target, for example ``app:app``.

        :returns: The object the target names.

        :raises ApplicationLoadError: If the target is malformed, the module
            cannot be imported, or the attribute does not exist. Errors raised
            by the module's own code while it is imported (a ``SyntaxError``,
            a failing import inside it) are chained as the cause.
    """
    module_path, attribute_path = parse_app_target(target)

    ensure_import_path()

    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as err:
        # Tell a missing application module apart from a module the
        # application itself failed to import.
        missing_name = err.name if err.name is not None else ""
        is_target_missing = module_path == missing_name or module_path.startswith(missing_name + ".")

        if is_target_missing:
            errmsg = "Could not import the application module '{}' (target '{}'): {}".format(
                module_path, target, err
            )
        else:
            errmsg = "The application module '{}' failed to import '{}': {}".format(
                module_path, missing_name, err
            )
        raise ApplicationLoadError(errmsg) from err
    except Exception as err:
        errmsg = "The application module '{}' raised {} while it was imported: {}".format(
            module_path, type(err).__name__, err
        )
        raise ApplicationLoadError(errmsg) from err

    application = module

    for part in attribute_path.split("."):
        if not hasattr(application, part):
            errmsg = "The module '{}' has no attribute '{}' (target '{}').".format(
                module_path, attribute_path, target
            )
            raise ApplicationLoadError(errmsg)
        application = getattr(application, part)

    return application


def find_webapp_persona(application: Any = None) -> Optional[Any]:
    """
        Find the :class:`WebApplication` persona that owns an application.

        An application module normally exposes the ASGI application as
        ``app``, while the router, the endpoint registry and the database
        hooks belong to the web application persona it established. When the
        loaded object is itself a ``WebApplication`` it is returned;
        otherwise the persona singleton is used.

        :param application: The object loaded from the import target.

        :returns: The ``WebApplication`` instance, or ``None`` when the
            application did not establish a persona.
    """
    from ccai.errors.exceptions import SemanticError
    from ccai.webworks.webapplication import WebApplication
    from ccai.webworks.wellknown import ThisWebApplicationSingleton

    persona = None

    if isinstance(application, WebApplication):
        persona = application
    else:
        try:
            persona = ThisWebApplicationSingleton()
        except SemanticError:
            # No persona was established by the application module; the
            # caller reports that it cannot find one.
            persona = None

    return persona
