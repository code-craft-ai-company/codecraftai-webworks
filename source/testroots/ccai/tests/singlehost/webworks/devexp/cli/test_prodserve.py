"""
    Tests for the ProdServeCommand class (``webworks prodserve``).

    The options are checked against the configuration they build. The
    command itself is run as ``python -m ccai.webworks.devexp.cli prodserve``
    in a child process serving a WebApplication on a port of 18100-18199.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

from typing import Any, Dict, List

from ccai.errors.exceptions import SkipError

from ccai.testshared.servers.serverprocess import ServerProcess, child_environment, find_free_port

from ccai.webworks.devexp.cli.exitcodes import EXIT_CONFIG_ERROR
from ccai.webworks.devexp.cli.prodserve import ProdServeCommand, load_production_application
from ccai.webworks.prodserver.exceptions import ConfigurationError
from ccai.webworks.prodserver.serverconfig import EXIT_APP_LOAD_ERROR, EXIT_SUCCESS


def _parse(arguments: List[str]) -> argparse.Namespace:
    """
        Parse prodserve arguments the way the CLI does.
    """
    parser = argparse.ArgumentParser(prog="webworks prodserve")
    command = ProdServeCommand()
    command.add_arguments(parser)
    rtnval = parser.parse_args(arguments)
    return rtnval


def test_options_build_the_server_configuration():
    """
        Command-line options become ServerConfig fields.
    """
    args = _parse([
        "--host", "127.0.0.1", "--port", "18120", "--workers", "3", "--threads", "8",
        "--max-requests", "500", "--max-requests-jitter", "50", "--timeout", "15",
        "--limit-request-body", "2048", "--pid-file", "/run/site.pid", "--umask", "027",
        "--log-format", "json", "--log-level", "warning", "--preload", "--ssl-redirect",
        "--health-check-path", "/healthz", "--trace-header", "X-Trace",
    ])

    config = ProdServeCommand().build_config(args, {})

    expected: Dict[str, Any] = {
        "host": "127.0.0.1",
        "port": 18120,
        "workers": 3,
        "threads": 8,
        "max_requests": 500,
        "max_requests_jitter": 50,
        "timeout": 15,
        "limit_request_body": 2048,
        "pid_file": "/run/site.pid",
        "umask": 0o027,
        "log_format": "json",
        "log_level": "WARNING",
        "preload": True,
        "ssl_redirect": True,
        "health_check_path": "/healthz",
        "trace_header": "X-Trace",
    }

    for name, value in expected.items():
        if getattr(config, name) != value:
            errmsg = f"Expected {name}={value!r}, got {getattr(config, name)!r}"
            raise AssertionError(errmsg)

    config.validate()

    return


def test_configuration_section_fills_in_and_options_win():
    """
        The prodserver section supplies options not given on the command
        line; strings from the environment are converted.
    """
    args = _parse(["--workers", "5"])
    section = {"prodserver": {"workers": "2", "threads": "4", "preload": "true", "max_requests": "none", "port": 9001}}

    config = ProdServeCommand().build_config(args, section)

    if (config.workers, config.threads, config.preload, config.max_requests, config.port) != (5, 4, True, None, 9001):
        errmsg = f"Expected workers 5, threads 4, preload, no max_requests, port 9001, got {config}"
        raise AssertionError(errmsg)

    return


def test_configuration_section_with_unknown_or_bad_keys_fails_early():
    """
        A key that is not an option, or a value that is not a number, is a
        configuration error.
    """
    for section in ({"prodserver": {"wrokers": 2}}, {"prodserver": {"workers": "many"}}, {"prodserver": {"on_starting": "x"}}):
        try:
            ProdServeCommand().build_config(_parse([]), section)
        except ConfigurationError:
            continue
        errmsg = f"Expected ConfigurationError for {section}"
        raise AssertionError(errmsg)

    return


def test_load_production_application_with_a_factory_target():
    """
        With --factory the target is called to get the application.
    """
    import ccai.testshared.servers.plainapps as plainapps

    application = load_production_application("ccai.testshared.servers.plainapps:make_wsgi_app", True)

    if application is not plainapps.wsgi_app:
        errmsg = f"Expected the application the factory returned, got {application!r}"
        raise AssertionError(errmsg)

    from ccai.webworks.devexp.apploader import ApplicationLoadError

    try:
        load_production_application("ccai.testshared.servers.plainapps:not_an_application", True)
    except ApplicationLoadError:
        return

    errmsg = "Expected ApplicationLoadError for a factory that cannot be called"
    raise AssertionError(errmsg)


def test_command_without_application_reports_a_configuration_error():
    """
        Without --app, server.app or ./app.py the command ends with EXIT_CONFIG_ERROR.
    """
    directory = tempfile.mkdtemp(prefix="prodserve-empty-")
    env = child_environment()
    env.pop("WEBWORKS_SERVER_APP", None)

    try:
        completed = subprocess.run(
            [sys.executable, "-m", "ccai.webworks.devexp.cli", "prodserve"],
            cwd=directory,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
    finally:
        shutil.rmtree(directory)

    if completed.returncode != EXIT_CONFIG_ERROR or "No application to serve" not in completed.stderr:
        errmsg = f"Expected {EXIT_CONFIG_ERROR} and a message, got {completed.returncode}:\n{completed.stderr}"
        raise AssertionError(errmsg)

    return


def test_command_serves_the_application_and_stops_on_sigterm():
    """
        webworks prodserve --app ... serves the WebApplication until SIGTERM
        and ends with exit code 0.
    """
    if not hasattr(os, "fork"):
        raise SkipError("The production server needs os.fork.")

    directory = tempfile.mkdtemp(prefix="prodserve-cli-")
    port = find_free_port()
    code = "import sys\nfrom ccai.webworks.devexp.cli.webworkscli import main\nsys.exit(main(sys.argv[1:]))\n"
    arguments = [
        "prodserve", "--app", "ccai.testshared.servers.servingsite:webapp",
        "--host", "127.0.0.1", "--port", str(port), "--log-format", "json", "--graceful-timeout", "5",
    ]
    env = {"SERVINGSITE_PRESENCE_DIR": directory, "WEBWORKS_PRODSERVER_WORKERS": "2"}

    try:
        server = ServerProcess(code, port, args=arguments, env=env)
        with server:
            status, headers, body = server.request("GET", "/hello")
            health_status, _, _ = server.request("GET", "/health")
        exit_code = server.returncode
        output = server.output()
    finally:
        shutil.rmtree(directory, ignore_errors=True)

    if status != 200 or body != b"hello" or "X-Request-ID" not in headers or health_status != 200:
        errmsg = f"Expected the application behind the production layer, got {status} {body!r} {health_status}"
        raise AssertionError(errmsg)

    if exit_code != EXIT_SUCCESS:
        errmsg = f"Expected exit code 0 after SIGTERM, got {exit_code}:\n{output}"
        raise AssertionError(errmsg)

    if "with 2 worker(s)" not in output:
        errmsg = f"Expected WEBWORKS_PRODSERVER_WORKERS to give two workers, output:\n{output}"
        raise AssertionError(errmsg)

    return


def test_command_with_a_target_that_cannot_be_loaded_ends_with_app_load_error():
    """
        A target whose module does not exist ends the command with
        EXIT_APP_LOAD_ERROR once the workers fail to load it.
    """
    if not hasattr(os, "fork"):
        raise SkipError("The production server needs os.fork.")

    port = find_free_port()

    completed = subprocess.run(
        [
            sys.executable, "-m", "ccai.webworks.devexp.cli", "prodserve",
            "--app", "ccai.testshared.servers.no_such_site:webapp",
            "--host", "127.0.0.1", "--port", str(port), "--workers", "1",
        ],
        env=child_environment(),
        capture_output=True,
        text=True,
        timeout=120,
    )

    if completed.returncode != EXIT_APP_LOAD_ERROR or "no_such_site" not in completed.stderr:
        errmsg = f"Expected {EXIT_APP_LOAD_ERROR} naming the target, got {completed.returncode}:\n{completed.stderr[-3000:]}"
        raise AssertionError(errmsg)

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
