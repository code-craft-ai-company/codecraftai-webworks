"""
    Unit tests for :mod:`automojo.webworks.security.signedserializer`.

    Covered:
        - A payload round-trips through ``dumps`` / ``loads``.
        - A tampered token is rejected.
        - A token signed with a different secret or a different salt
          is rejected.
        - A token older than ``max_age`` is rejected, while a fresh
          token within ``max_age`` is accepted.
        - Structurally malformed tokens are rejected.
        - An empty secret is rejected at construction.
"""

import pytest

from automojo.webworks.security.signedserializer import (
    BadPayloadError,
    BadSignatureError,
    BadTimeSignatureError,
    TimedSerializer,
)


def test_round_trip_recovers_payload():
    serializer = TimedSerializer("super-secret", salt="oauth-state")

    payload = {"provider": "google", "state": "abc", "nonce": "xyz", "register": True}
    token = serializer.dumps(payload)
    recovered = serializer.loads(token, max_age=600)

    if recovered != payload:
        raise AssertionError("Round-trip payload mismatch: {!r}".format(recovered))

    return


def test_tampered_token_is_rejected():
    serializer = TimedSerializer("super-secret", salt="oauth-state")

    token = serializer.dumps({"state": "abc"})
    payload_segment, timestamp_segment, signature_segment = token.split(".")
    # Flip a character in the payload segment while leaving the
    # signature untouched.
    tampered_payload = ("A" if payload_segment[0] != "A" else "B") + payload_segment[1:]
    tampered = "{}.{}.{}".format(tampered_payload, timestamp_segment, signature_segment)

    with pytest.raises(BadSignatureError):
        serializer.loads(tampered, max_age=600)

    return


def test_wrong_secret_is_rejected():
    producer = TimedSerializer("secret-one", salt="oauth-state")
    consumer = TimedSerializer("secret-two", salt="oauth-state")

    token = producer.dumps({"state": "abc"})

    with pytest.raises(BadSignatureError):
        consumer.loads(token, max_age=600)

    return


def test_wrong_salt_is_rejected():
    producer = TimedSerializer("shared-secret", salt="salt-one")
    consumer = TimedSerializer("shared-secret", salt="salt-two")

    token = producer.dumps({"state": "abc"})

    with pytest.raises(BadSignatureError):
        consumer.loads(token, max_age=600)

    return


def test_token_older_than_max_age_is_rejected():
    serializer = TimedSerializer("super-secret", salt="oauth-state")

    token = serializer.dumps({"state": "abc"})

    # A negative max_age means "already too old" without having to sleep.
    with pytest.raises(BadTimeSignatureError):
        serializer.loads(token, max_age=-1)

    return


def test_token_within_max_age_is_accepted():
    serializer = TimedSerializer("super-secret", salt="oauth-state")

    token = serializer.dumps({"state": "abc"})
    recovered = serializer.loads(token, max_age=3600)

    if recovered != {"state": "abc"}:
        raise AssertionError("Fresh token should validate within max_age")

    return


def test_no_max_age_skips_expiry_check():
    serializer = TimedSerializer("super-secret", salt="oauth-state")

    token = serializer.dumps({"state": "abc"})
    recovered = serializer.loads(token)

    if recovered != {"state": "abc"}:
        raise AssertionError("Token should validate when no max_age is supplied")

    return


def test_malformed_token_is_rejected():
    serializer = TimedSerializer("super-secret", salt="oauth-state")

    with pytest.raises(BadPayloadError):
        serializer.loads("only-two.segments", max_age=600)

    return


def test_empty_secret_is_rejected():
    with pytest.raises(ValueError):
        TimedSerializer("", salt="oauth-state")

    return
