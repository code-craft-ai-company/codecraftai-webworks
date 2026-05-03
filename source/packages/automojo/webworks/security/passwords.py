"""
.. module:: passwords
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Password hashing and verification utilities backed by
        the Python standard library.

.. moduleauthor:: Automation Mojo LLC

This module provides :func:`hash_password` and
:func:`verify_password`, a pure-stdlib implementation of PBKDF2-SHA256
password hashing whose stored format is wire-compatible with the
``pbkdf2:sha256:<iterations>$<salt>$<hexhash>`` shape produced by
``werkzeug.security.generate_password_hash``. Webworks consumers can
adopt this module without re-hashing existing user records — hashes
that were minted by werkzeug remain verifiable, and hashes minted by
:func:`hash_password` are verifiable by werkzeug as well during any
mixed-deployment transition.

The module deliberately does **not** depend on werkzeug or any
third-party password hashing library. Format strings are parsed by
hand and the heavy lifting is delegated to
:func:`hashlib.pbkdf2_hmac` from the standard library.

Algorithm choice
----------------

PBKDF2-HMAC-SHA256 with 600,000 iterations is the default. This
matches werkzeug's current default and OWASP's 2023 password storage
guidance. The iteration count is encoded in the stored hash so future
adjustments don't require a migration: existing hashes verify against
the stored count, and re-hashes (during password reset / login)
adopt the new default automatically.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


import hashlib
import hmac
import secrets
import string


# Default PBKDF2 iteration count. Matches werkzeug 2.3+ and the OWASP
# 2023 guidance for PBKDF2-HMAC-SHA256.
DEFAULT_ITERATIONS: int = 600_000


# Default salt length in characters. Werkzeug uses 16 by default;
# matched here for interop and because 16 alphanumerics ≈ 95 bits
# of entropy, comfortably above any realistic threat model for
# password salts.
DEFAULT_SALT_LENGTH: int = 16


# Salt characters. Constrained to alphanumeric ASCII so the salt can
# be embedded directly in the format string without escaping. Matches
# werkzeug's salt alphabet.
_SALT_ALPHABET: str = string.ascii_letters + string.digits


def _generate_salt(length: int = DEFAULT_SALT_LENGTH) -> str:
    """
        Generate a fresh cryptographically random salt.

        :param length: Number of characters in the resulting salt.
                       Must be a positive integer; values below 8 are
                       silently raised to 8 to keep the salt useful
                       against rainbow tables.

        :returns: A random alphanumeric ASCII string of *length*
                  characters.
    """
    if length < 8:
        length = 8

    rtnval = "".join(secrets.choice(_SALT_ALPHABET) for _ in range(length))
    return rtnval


def _pbkdf2_hex(
    password: str,
    salt: str,
    iterations: int,
    hash_name: str = "sha256",
) -> str:
    """
        Compute PBKDF2-HMAC and return the lowercase hex digest.

        :param password: The plaintext password.
        :param salt: The salt string. Encoded as UTF-8 before
                     mixing into the KDF.
        :param iterations: Number of PBKDF2 iterations.
        :param hash_name: Hash function name passed through to
                          :func:`hashlib.pbkdf2_hmac`. Defaults to
                          ``"sha256"``.

        :returns: Hex-encoded derived key.
    """
    password_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")

    derived = hashlib.pbkdf2_hmac(
        hash_name,
        password_bytes,
        salt_bytes,
        iterations,
    )

    rtnval = derived.hex()
    return rtnval


def hash_password(
    password: str,
    *,
    iterations: int = DEFAULT_ITERATIONS,
    salt_length: int = DEFAULT_SALT_LENGTH,
) -> str:
    """
        Hash a plaintext password for storage.

        Produces a string in the wire-compatible format
        ``pbkdf2:sha256:<iterations>$<salt>$<hexhash>`` that any
        consumer of werkzeug-style password hashes can verify. The
        format is also what :func:`verify_password` reads on the
        return trip.

        :param password: The plaintext password to hash.
        :param iterations: PBKDF2 iteration count. Defaults to
                           :data:`DEFAULT_ITERATIONS`. Increase this
                           in lockstep with hardware advances; older
                           hashes verify against their stored count
                           regardless of the current default.
        :param salt_length: Number of characters in the random salt.
                            Defaults to :data:`DEFAULT_SALT_LENGTH`.

        :returns: A stored-hash string ready to persist in the user
                  table.
        :raises TypeError: If *password* is not a string.
    """
    if not isinstance(password, str):
        raise TypeError("password must be a str")

    salt = _generate_salt(length=salt_length)
    hashed = _pbkdf2_hex(password, salt, iterations)

    rtnval = "pbkdf2:sha256:{iter}${salt}${hashed}".format(
        iter=iterations,
        salt=salt,
        hashed=hashed,
    )
    return rtnval


def verify_password(password: str, stored: str) -> bool:
    """
        Verify a plaintext password against a stored hash.

        Accepts the format produced by :func:`hash_password` —
        ``pbkdf2:<hash>:<iterations>$<salt>$<hexhash>`` — which is
        also the format ``werkzeug.security.generate_password_hash``
        produces for the ``pbkdf2:sha256`` method. The legacy
        ``pbkdf2:<hash>`` shape (no explicit iteration count) is
        also accepted; the iteration count falls through to the
        current :data:`DEFAULT_ITERATIONS`.

        Comparison uses :func:`hmac.compare_digest` so an attacker
        that can time the call cannot learn anything about the
        stored hash.

        Malformed inputs (missing fields, unknown method, non-numeric
        iteration count, non-string arguments) all return ``False``
        rather than raising, so callers do not need to wrap calls in
        defensive try/excepts at the credential-check site.

        :param password: The plaintext password supplied by the
                         client.
        :param stored: The stored-hash string previously produced
                       by :func:`hash_password` (or a werkzeug-
                       compatible equivalent).

        :returns: ``True`` when *password* matches *stored*,
                  ``False`` otherwise.
    """
    if not isinstance(password, str):
        return False
    if not isinstance(stored, str):
        return False
    if stored == "":
        return False

    parts = stored.split("$", 2)
    if len(parts) != 3:
        return False

    method_spec = parts[0]
    salt = parts[1]
    expected_hash = parts[2]

    if salt == "" or expected_hash == "":
        return False

    method_segments = method_spec.split(":")
    if len(method_segments) < 2:
        return False

    if method_segments[0] != "pbkdf2":
        return False

    hash_name = method_segments[1]

    if len(method_segments) >= 3:
        iterations_text = method_segments[2]
        if not iterations_text.isdigit():
            return False
        iterations = int(iterations_text)
        if iterations <= 0:
            return False
    else:
        iterations = DEFAULT_ITERATIONS

    try:
        derived_hash = _pbkdf2_hex(
            password=password,
            salt=salt,
            iterations=iterations,
            hash_name=hash_name,
        )
    except (ValueError, TypeError):
        # Unknown hash_name or other PBKDF2 input failure; treat as
        # verification failure rather than propagating the exception
        # — the credential-check call site doesn't want to leak the
        # specific reason.
        return False

    rtnval = hmac.compare_digest(derived_hash, expected_hash)
    return rtnval


__all__ = [
    "DEFAULT_ITERATIONS",
    "DEFAULT_SALT_LENGTH",
    "hash_password",
    "verify_password",
]
