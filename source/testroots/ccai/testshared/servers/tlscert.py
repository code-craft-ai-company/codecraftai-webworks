"""
    Throwaway TLS certificates for the server tests.
"""

import os
import shutil
import subprocess

from typing import Tuple

from ccai.errors.exceptions import SkipError


def create_self_signed_certificate(directory: str) -> Tuple[str, str]:
    """
        Create a self-signed certificate for 127.0.0.1 and its private key.

        The standard library cannot create certificates, so the openssl
        command line is used; a test that needs one is skipped where it is
        not installed.

        :param directory: Directory to write the files to.

        :returns: The certificate file and the key file.

        :raises SkipError: If openssl is not available.
    """
    openssl = shutil.which("openssl")
    if openssl is None:
        raise SkipError("openssl is not available to create a test certificate.")

    certfile = os.path.join(directory, "server-cert.pem")
    keyfile = os.path.join(directory, "server-key.pem")

    subprocess.run(
        [
            openssl, "req", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-keyout", keyfile,
            "-out", certfile,
            "-days", "1",
            "-subj", "/CN=127.0.0.1",
        ],
        check=True,
        capture_output=True,
        timeout=60,
    )

    rtnval = (certfile, keyfile)
    return rtnval
