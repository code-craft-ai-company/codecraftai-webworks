"""
    Standard exit codes for the webworks CLI.

    This module defines the exit code constants used by the CLI
    framework to communicate the outcome of command execution to
    the calling process. Each exit code represents a specific
    category of result, allowing callers to distinguish between
    successful execution, general errors, usage errors, and
    configuration problems.

    Exit codes follow common Unix conventions where zero indicates
    success and non-zero values indicate different categories of
    failure.
"""


EXIT_SUCCESS = 0
"""Exit code indicating the command completed successfully."""

EXIT_ERROR = 1
"""Exit code indicating a general error occurred during execution."""

EXIT_USAGE_ERROR = 2
"""Exit code indicating incorrect command usage or missing arguments."""

EXIT_CONFIG_ERROR = 3
"""Exit code indicating a configuration loading or parsing failure."""

EXIT_NOT_FOUND = 4
"""Exit code indicating a requested resource was not found."""
