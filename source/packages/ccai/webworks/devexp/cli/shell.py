"""
    CLI shell command for the webworks developer experience.

    This module provides the :class:`ShellCommand` that starts an
    interactive Python shell with the application instance and common
    imports pre-loaded. The command supports IPython when available,
    falling back to the standard Python interactive console.

    The shell loads a startup file (``.webworks_shell.py``) from the
    current working directory if present, and displays a banner showing
    all available pre-loaded objects.

    The shell-launching logic is separated from the setup and
    configuration logic to support testability without blocking on
    interactive input.
"""

import code
import os
import sys

from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

from ccai.webworks.devexp.cli.command import CLICommand
from ccai.webworks.devexp.cli.exitcodes import EXIT_CONFIG_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_SUCCESS

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


# =============================================================================
# Constants
# =============================================================================

DEFAULT_STARTUP_FILENAME = ".webworks_shell.py"
"""Default filename for the shell startup script."""

DEFAULT_COMMON_IMPORTS = {
    "os": os,
    "sys": sys,
}
"""Default common imports pre-loaded into the shell namespace."""


# =============================================================================
# Application Interface
# =============================================================================


class ShellApplication:
    """
        Abstract interface for the application provided to the shell.

        Users of the framework provide a concrete implementation of this
        class to supply the application instance and common imports for
        the interactive shell. The CLI shell command delegates application
        retrieval to this interface, keeping the CLI framework independent
        of any specific application implementation.
    """

    def get_instance(self) -> Any:
        """
            Get the application instance to pre-load into the shell.

            :returns: The application instance.

            :raises: NotImplementedError
        """
        raise NotImplementedError("Subclasses must implement the get_instance method.")

    def get_common_imports(self) -> Dict[str, Any]:
        """
            Get common imports to pre-load into the shell namespace.

            Returns a dictionary mapping names to objects that should
            be available in the shell namespace. These typically include
            models, utilities, and other frequently used modules.

            :returns: A dictionary of name-to-object mappings.

            :raises: NotImplementedError
        """
        raise NotImplementedError("Subclasses must implement the get_common_imports method.")


# =============================================================================
# Helper Functions
# =============================================================================

def resolve_shell_app(config: Dict[str, Any]) -> Optional[ShellApplication]:
    """
        Resolve the shell application from configuration.

        Looks for a ``shell_app`` key in the configuration dictionary.
        The value must be an instance of :class:`ShellApplication`.

        :param config: Loaded configuration dictionary.

        :returns: The shell application instance or None if not configured.
    """
    shell_app = config.get("shell_app", None)

    if shell_app is not None and isinstance(shell_app, ShellApplication):
        return shell_app

    return None


def build_shell_namespace(
    shell_app: Optional[ShellApplication],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
        Build the namespace dictionary for the interactive shell.

        The namespace includes the application instance (as ``app``),
        common imports from the application, and the default common
        imports (``os``, ``sys``).

        :param shell_app: The shell application interface or None.
        :param config: Loaded configuration dictionary.

        :returns: A dictionary of names to objects for the shell namespace.
    """
    namespace = {}

    namespace.update(DEFAULT_COMMON_IMPORTS)

    if shell_app is not None:
        try:
            app_instance = shell_app.get_instance()
            namespace["app"] = app_instance
        except Exception:
            pass

        try:
            common_imports = shell_app.get_common_imports()
            if isinstance(common_imports, dict):
                namespace.update(common_imports)
        except Exception:
            pass

    return namespace


def build_banner(namespace: Dict[str, Any]) -> str:
    """
        Build the banner text showing available pre-loaded objects.

        The banner lists all objects available in the shell namespace
        with their type names, formatted for readability.

        :param namespace: The shell namespace dictionary.

        :returns: A formatted banner string.
    """
    lines = []

    lines.append("Webworks Interactive Shell")
    lines.append("")
    lines.append("Available objects:")

    sorted_names = sorted(namespace.keys())

    for name in sorted_names:
        obj = namespace[name]
        type_name = type(obj).__name__

        if callable(obj) and not isinstance(obj, type):
            kind = "function"
        elif isinstance(obj, type):
            kind = "class"
        else:
            kind = type_name

        lines.append("  {} - {}".format(name, kind))

    lines.append("")

    return "\n".join(lines)


def load_startup_file(
    startup_path: str,
    namespace: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """
        Load and execute a startup file in the shell namespace.

        If the startup file exists, its contents are compiled and
        executed in the provided namespace. Any names defined in the
        startup file become available in the shell.

        :param startup_path: Path to the startup file.
        :param namespace: The shell namespace to execute the file in.

        :returns: A tuple of (loaded, error_message). ``loaded`` is True
            if the file was found and executed successfully. ``error_message``
            is None on success or a string describing the error.
    """
    if not os.path.isfile(startup_path):
        return (False, None)

    try:
        with open(startup_path, "r") as fh:
            source = fh.read()

        compiled = compile(source, startup_path, "exec")
        exec(compiled, namespace)  # noqa: S102

        return (True, None)

    except Exception as err:
        error_message = "Error loading startup file '{}': {}".format(
            startup_path, str(err)
        )
        return (False, error_message)


def check_ipython_available() -> bool:
    """
        Check whether IPython is available for import.

        :returns: True if IPython can be imported.
    """
    try:
        import IPython  # noqa: F401
        return True
    except ImportError:
        return False


def start_ipython_shell(namespace: Dict[str, Any], banner: str) -> None:
    """
        Start an IPython interactive shell.

        This function is separated from the command logic to allow
        testing the setup and configuration without blocking on
        interactive input.

        :param namespace: The namespace dictionary for the shell.
        :param banner: The banner text to display on startup.
    """
    import IPython
    IPython.start_ipython(argv=[], user_ns=namespace, display_banner=True)

    return


def start_standard_shell(namespace: Dict[str, Any], banner: str) -> None:
    """
        Start a standard Python interactive shell.

        This function is separated from the command logic to allow
        testing the setup and configuration without blocking on
        interactive input.

        :param namespace: The namespace dictionary for the shell.
        :param banner: The banner text to display on startup.
    """
    console = code.InteractiveConsole(locals=namespace)
    console.interact(banner=banner)

    return


# =============================================================================
# ShellCommand
# =============================================================================

class ShellCommand(CLICommand):
    """
        CLI command for starting an interactive Python shell.

        The ``shell`` command starts an interactive Python shell with
        the application instance and common imports pre-loaded. It
        supports IPython when available, falling back to the standard
        Python interactive console.

        A startup file (``.webworks_shell.py``) is loaded from the
        current working directory if present. A banner displays all
        available pre-loaded objects.

        The shell-launching logic is delegated to replaceable launcher
        functions, allowing the setup and configuration logic to be
        tested without blocking on interactive input.

        Usage::

            webworks shell
            webworks shell --no-ipython
            webworks shell --startup-file custom_startup.py
            webworks shell --no-banner
    """

    name = "shell"
    help = "Start an interactive Python shell with the application pre-loaded."

    def __init__(self):
        """
            Initialize the ShellCommand.

            The ``_ipython_launcher`` and ``_standard_launcher`` attributes
            hold the functions used to start the interactive shell. They
            can be replaced for testing purposes.
        """
        self._ipython_launcher: Callable[[Dict[str, Any], str], None] = start_ipython_shell
        self._standard_launcher: Callable[[Dict[str, Any], str], None] = start_standard_shell
        self._ipython_checker: Callable[[], bool] = check_ipython_available

        return

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add command-specific arguments to the parser.

            Registers the ``--no-ipython``, ``--startup-file``, and
            ``--no-banner`` options.

            :param parser: The argument parser to add arguments to.
        """
        parser.add_argument(
            "--no-ipython",
            action="store_true",
            default=False,
            dest="no_ipython",
            help="Disable IPython even if installed. Use standard Python shell."
        )

        parser.add_argument(
            "--startup-file",
            type=str,
            default=None,
            dest="startup_file",
            help="Path to a startup file to load. Defaults to '{}' in the current directory.".format(
                DEFAULT_STARTUP_FILENAME
            )
        )

        parser.add_argument(
            "--no-banner",
            action="store_true",
            default=False,
            dest="no_banner",
            help="Suppress the startup banner."
        )

        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the shell command.

            Resolves the shell application from configuration, builds
            the namespace with pre-loaded objects, loads the startup
            file if present, builds the banner, and launches the
            interactive shell.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code where 0 indicates success.
        """
        shell_app = resolve_shell_app(config)

        namespace = build_shell_namespace(shell_app, config)

        startup_file = getattr(args, "startup_file", None)

        if startup_file is None:
            startup_file = os.path.join(os.getcwd(), DEFAULT_STARTUP_FILENAME)

        loaded, error_message = load_startup_file(startup_file, namespace)

        if error_message is not None:
            print(error_message)
            return EXIT_ERROR

        no_banner = getattr(args, "no_banner", False)

        if no_banner:
            banner = ""
        else:
            banner = build_banner(namespace)

        no_ipython = getattr(args, "no_ipython", False)

        use_ipython = (not no_ipython) and self._ipython_checker()

        try:
            if use_ipython:
                self._ipython_launcher(namespace, banner)
            else:
                self._standard_launcher(namespace, banner)
        except SystemExit:
            pass
        except Exception as err:
            errmsg = "Error starting shell: {}".format(str(err))
            print(errmsg)
            return EXIT_ERROR

        return EXIT_SUCCESS
