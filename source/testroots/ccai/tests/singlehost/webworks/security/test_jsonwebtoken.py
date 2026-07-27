"""
    Unit tests for :mod:`ccai.webworks.security.jsonwebtoken`.

    Covered:
        - RS256 and ES256 round-trip decode + signature verification
          against a JWKS, using tokens signed independently with
          :mod:`cryptography`.
        - Tampered payloads and wrong-key signatures are rejected.
        - The ``algorithms`` allow-list defeats algorithm confusion
          (a token whose ``alg`` is not permitted is rejected even
          when the signature would otherwise verify).
        - JWKS key selection by ``kid``.
        - ``ClaimsRegistry`` enforces ``essential`` / ``value`` claims
          plus the ``exp`` / ``nbf`` time windows.
"""

import base64
import json
import time

from typing import Any, Dict, Tuple


from ccai.webworks.security import jsonwebtoken as jwt
from ccai import testbase


# =============================================================================
# Helpers
# =============================================================================


def _b64url(data: bytes) -> str:
    rtnval = base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")
    return rtnval


def _int_to_b64url(value: int) -> str:
    byte_length = (value.bit_length() + 7) // 8
    raw = value.to_bytes(byte_length, byteorder="big")
    rtnval = _b64url(raw)
    return rtnval


def _make_rs256(claims: Dict[str, Any], kid: str) -> Tuple[str, Dict[str, Any]]:
    """
        Sign an RS256 JWT and return (token, jwks).
    """
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    header = {"alg": "RS256", "typ": "JWT", "kid": kid}
    header_segment = _b64url(json.dumps(header).encode("utf-8"))
    payload_segment = _b64url(json.dumps(claims).encode("utf-8"))
    signing_input = "{}.{}".format(header_segment, payload_segment).encode("ascii")

    signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    token = "{}.{}.{}".format(header_segment, payload_segment, _b64url(signature))

    numbers = private_key.public_key().public_numbers()
    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": kid,
                "alg": "RS256",
                "n": _int_to_b64url(numbers.n),
                "e": _int_to_b64url(numbers.e),
            }
        ]
    }
    return token, jwks


def _make_es256(claims: Dict[str, Any], kid: str) -> Tuple[str, Dict[str, Any]]:
    """
        Sign an ES256 JWT and return (token, jwks).
    """
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import (
        decode_dss_signature,
    )

    private_key = ec.generate_private_key(ec.SECP256R1())

    header = {"alg": "ES256", "typ": "JWT", "kid": kid}
    header_segment = _b64url(json.dumps(header).encode("utf-8"))
    payload_segment = _b64url(json.dumps(claims).encode("utf-8"))
    signing_input = "{}.{}".format(header_segment, payload_segment).encode("ascii")

    der_signature = private_key.sign(signing_input, ec.ECDSA(hashes.SHA256()))
    r_value, s_value = decode_dss_signature(der_signature)
    raw_signature = r_value.to_bytes(32, "big") + s_value.to_bytes(32, "big")
    token = "{}.{}.{}".format(header_segment, payload_segment, _b64url(raw_signature))

    numbers = private_key.public_key().public_numbers()
    jwks = {
        "keys": [
            {
                "kty": "EC",
                "kid": kid,
                "crv": "P-256",
                "x": _int_to_b64url(numbers.x),
                "y": _int_to_b64url(numbers.y),
            }
        ]
    }
    return token, jwks


def _baseline_claims() -> Dict[str, Any]:
    rtnval = {
        "iss": "https://issuer.example.com",
        "aud": "client-123",
        "sub": "subject-1",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return rtnval


# =============================================================================
# Round-trip decode
# =============================================================================


def test_rs256_round_trip_decodes_claims():
    token, jwks = _make_rs256(_baseline_claims(), kid="rsa-1")
    key_set = jwt.JsonWebKeySet.import_key_set(jwks)

    decoded = jwt.decode(token, key=key_set, algorithms=["RS256"])

    if decoded.claims.get("sub") != "subject-1":
        raise AssertionError("RS256 round-trip lost the sub claim")

    return


def test_es256_round_trip_decodes_claims():
    token, jwks = _make_es256(_baseline_claims(), kid="ec-1")
    key_set = jwt.JsonWebKeySet.import_key_set(jwks)

    decoded = jwt.decode(token, key=key_set, algorithms=["ES256"])

    if decoded.claims.get("sub") != "subject-1":
        raise AssertionError("ES256 round-trip lost the sub claim")

    return


# =============================================================================
# Signature rejection
# =============================================================================


def test_tampered_payload_is_rejected():
    token, jwks = _make_rs256(_baseline_claims(), kid="rsa-1")
    key_set = jwt.JsonWebKeySet.import_key_set(jwks)

    header_segment, _payload_segment, signature_segment = token.split(".")
    forged_payload = _b64url(json.dumps({"sub": "attacker"}).encode("utf-8"))
    forged = "{}.{}.{}".format(header_segment, forged_payload, signature_segment)

    with testbase.raises(jwt.InvalidSignatureError):
        jwt.decode(forged, key=key_set, algorithms=["RS256"])

    return


def test_wrong_key_is_rejected():
    token, _jwks = _make_rs256(_baseline_claims(), kid="rsa-1")
    _other_token, other_jwks = _make_rs256(_baseline_claims(), kid="rsa-1")
    other_key_set = jwt.JsonWebKeySet.import_key_set(other_jwks)

    with testbase.raises(jwt.InvalidSignatureError):
        jwt.decode(token, key=other_key_set, algorithms=["RS256"])

    return


def test_algorithm_not_in_allow_list_is_rejected():
    token, jwks = _make_rs256(_baseline_claims(), kid="rsa-1")
    key_set = jwt.JsonWebKeySet.import_key_set(jwks)

    with testbase.raises(jwt.UnsupportedAlgorithmError):
        jwt.decode(token, key=key_set, algorithms=["ES256"])

    return


def test_empty_allow_list_is_rejected():
    token, jwks = _make_rs256(_baseline_claims(), kid="rsa-1")
    key_set = jwt.JsonWebKeySet.import_key_set(jwks)

    with testbase.raises(jwt.UnsupportedAlgorithmError):
        jwt.decode(token, key=key_set, algorithms=[])

    return


def test_malformed_token_is_rejected():
    with testbase.raises(jwt.DecodeError):
        jwt.decode("not-a-valid-token", key="secret", algorithms=["HS256"])

    return


# =============================================================================
# JWKS key selection
# =============================================================================


def test_jwks_selects_key_by_kid():
    token_a, jwks_a = _make_rs256(_baseline_claims(), kid="key-a")
    _token_b, jwks_b = _make_rs256(_baseline_claims(), kid="key-b")

    combined = {"keys": jwks_a["keys"] + jwks_b["keys"]}
    key_set = jwt.JsonWebKeySet.import_key_set(combined)

    decoded = jwt.decode(token_a, key=key_set, algorithms=["RS256"])
    if decoded.claims.get("sub") != "subject-1":
        raise AssertionError("kid selection failed to decode token A")

    return


def test_jwks_unmatched_kid_raises():
    token, jwks = _make_rs256(_baseline_claims(), kid="key-a")
    # Re-label the only key so the token's kid no longer matches.
    jwks["keys"][0]["kid"] = "different-kid"
    key_set = jwt.JsonWebKeySet.import_key_set(jwks)

    with testbase.raises(jwt.JoseError):
        jwt.decode(token, key=key_set, algorithms=["RS256"])

    return


def test_empty_jwks_raises():
    with testbase.raises(jwt.JoseError):
        jwt.JsonWebKeySet.import_key_set({"keys": []})

    return


# =============================================================================
# ClaimsRegistry
# =============================================================================


def test_claims_registry_accepts_matching_claims():
    claims = _baseline_claims()
    registry = jwt.ClaimsRegistry(
        {
            "iss": {"essential": True, "value": "https://issuer.example.com"},
            "aud": {"essential": True, "value": "client-123"},
        }
    )

    registry.validate(claims)

    return


def test_claims_registry_rejects_missing_essential_claim():
    claims = _baseline_claims()
    del claims["iss"]
    registry = jwt.ClaimsRegistry({"iss": {"essential": True}})

    with testbase.raises(jwt.InvalidClaimError):
        registry.validate(claims)

    return


def test_claims_registry_rejects_wrong_value():
    claims = _baseline_claims()
    registry = jwt.ClaimsRegistry(
        {"aud": {"essential": True, "value": "a-different-client"}}
    )

    with testbase.raises(jwt.InvalidClaimError):
        registry.validate(claims)

    return


def test_claims_registry_matches_value_inside_list():
    claims = _baseline_claims()
    claims["aud"] = ["other-client", "client-123"]
    registry = jwt.ClaimsRegistry({"aud": {"essential": True, "value": "client-123"}})

    registry.validate(claims)

    return


def test_claims_registry_rejects_expired_token():
    claims = _baseline_claims()
    claims["exp"] = int(time.time()) - 10
    registry = jwt.ClaimsRegistry({})

    with testbase.raises(jwt.InvalidClaimError):
        registry.validate(claims)

    return


def test_claims_registry_rejects_not_yet_valid_token():
    claims = _baseline_claims()
    claims["nbf"] = int(time.time()) + 3600
    registry = jwt.ClaimsRegistry({})

    with testbase.raises(jwt.InvalidClaimError):
        registry.validate(claims)

    return
