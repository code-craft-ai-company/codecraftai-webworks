"""
.. module:: test_validation_pydantic
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for validating request bodies against Pydantic models,
               above all the partial validation of a PATCH body.

    A PATCH body is validated field by field as a full request would be:
    type, ``Field()`` constraints, field validators, a nested model in full
    and the model's policy for unknown keys. Only the fields the client sent
    come back, as a dict. Model validators, which check a whole resource,
    do not run on a partial body.

    Pydantic is an optional extra of the package and a development
    dependency, so these tests run in a ``poetry install`` environment.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import json

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ccai.webworks.endpoints.registry import EndpointRegistry
from ccai.webworks.endpoints.rest import Validator, ValidationError, create_rest_middleware
from ccai.webworks.endpoints.rest.middleware import get_rest_payload
from ccai.webworks.endpoints.restendpoint import RestEndpoint
from ccai.webworks.routing.request import Request


# =============================================================================
# Test Models
# =============================================================================

class Address(BaseModel):
    """A nested model with a constrained field."""
    city: str
    zip_code: str = Field(pattern=r"^\d{5}$")


class Member(BaseModel):
    """A model with constraints, an alias, a field validator and model validators."""
    name: str = Field(min_length=2)
    age: int = Field(ge=0)
    email: str
    nickname: Optional[str] = None
    display_name: str = Field(default="", alias="displayName")
    address: Optional[Address] = None
    tags: List[str] = Field(default_factory=list)

    @field_validator("email")
    @classmethod
    def email_has_an_at_sign(cls, value: str) -> str:
        if "@" not in value:
            raise ValueError("an email address needs an @")
        return value

    @model_validator(mode="before")
    @classmethod
    def requires_a_name_key(cls, data):
        # Fails on a body without a name: it must not run on a partial body.
        if isinstance(data, dict) and "name" not in data:
            raise ValueError("the whole member is required")
        return data

    @model_validator(mode="after")
    def minors_have_a_nickname(self):
        if self.age < 18 and self.nickname is None:
            raise ValueError("a member under 18 needs a nickname")
        return self


class Closed(BaseModel):
    """A model that forbids unknown keys and validates its defaults."""
    model_config = ConfigDict(extra="forbid", validate_default=True)
    count: int
    label: str = "none"


class Open(BaseModel):
    """A model that keeps unknown keys."""
    model_config = ConfigDict(extra="allow")
    count: int


def _partial_errors(data: Dict, schema=Member) -> Dict[str, str]:
    """Validate ``data`` partially and return its field errors by field, or {} when it is valid."""
    errors = {}
    try:
        Validator().validate(data, schema, partial=True)
    except ValidationError as error:
        errors = {field_error.field: field_error.code for field_error in error.field_errors}
    return errors


# =============================================================================
# Partial (PATCH) validation
# =============================================================================

def test_partial_pydantic_rejects_values_of_the_wrong_type():
    """WW-0089: a PATCH body is no longer copied in unvalidated; {'age': 'x', 'email': 42} fails on both fields."""
    errors = _partial_errors({"age": "x", "email": 42})

    if sorted(errors) != ["age", "email"]:
        raise AssertionError(f"Expected field errors for 'age' and 'email', got {errors}")


def test_partial_pydantic_applies_field_constraints():
    """Field() limits apply to the fields a PATCH body sends."""
    errors = _partial_errors({"age": -1, "name": "A"})

    if errors != {"age": "greater_than_equal", "name": "string_too_short"}:
        raise AssertionError(f"Expected the ge and min_length errors, got {errors}")


def test_partial_pydantic_runs_field_validators():
    """A field validator of the model runs on a field the PATCH body sends."""
    errors = _partial_errors({"email": "nobody"})

    if errors != {"email": "value_error"}:
        raise AssertionError(f"Expected the email validator's error, got {errors}")


def test_partial_pydantic_returns_only_the_fields_sent():
    """The payload is a dict of the sent fields, converted; defaults of unsent fields are not filled in."""
    result = Validator().validate({"age": "7", "tags": ["a"]}, Member, partial=True)

    if result != {"age": 7, "tags": ["a"]}:
        raise AssertionError(f"Expected {{'age': 7, 'tags': ['a']}}, got {result!r}")


def test_partial_pydantic_empty_body_is_an_empty_update():
    """An empty PATCH body is valid and changes nothing."""
    result = Validator().validate({}, Member, partial=True)

    if result != {}:
        raise AssertionError(f"Expected an empty dict, got {result!r}")


def test_partial_pydantic_null_follows_the_field_type():
    """null clears an Optional field and is rejected for a field that is not nullable."""
    cleared = Validator().validate({"nickname": None}, Member, partial=True)
    errors = _partial_errors({"name": None})

    if cleared != {"nickname": None}:
        raise AssertionError(f"Expected {{'nickname': None}}, got {cleared!r}")

    if errors != {"name": "string_type"}:
        raise AssertionError(f"Expected a type error for a null name, got {errors}")


def test_partial_pydantic_reads_aliases_and_returns_field_names():
    """A field sent under its alias comes back under its field name."""
    result = Validator().validate({"displayName": "Ada"}, Member, partial=True)

    if result != {"display_name": "Ada"}:
        raise AssertionError(f"Expected {{'display_name': 'Ada'}}, got {result!r}")


def test_partial_pydantic_validates_a_nested_model_in_full():
    """A nested model sent in a PATCH body is validated in full, with its errors under the field's path."""
    missing = _partial_errors({"address": {"city": "Austin"}})
    malformed = _partial_errors({"address": {"city": "Austin", "zip_code": "7870"}})
    result = Validator().validate({"address": {"city": "Austin", "zip_code": "78701"}}, Member, partial=True)

    if missing != {"address.zip_code": "missing"}:
        raise AssertionError(f"Expected address.zip_code to be required, got {missing}")

    if malformed != {"address.zip_code": "string_pattern_mismatch"}:
        raise AssertionError(f"Expected a pattern error for address.zip_code, got {malformed}")

    if result != {"address": Address(city="Austin", zip_code="78701")}:
        raise AssertionError(f"Expected a validated Address, got {result!r}")


def test_partial_pydantic_lists_are_checked_per_element():
    """Elements of a list field are validated, each under its own path."""
    errors = _partial_errors({"tags": ["a", 3]})

    if errors != {"tags.1": "string_type"}:
        raise AssertionError(f"Expected an error for tags.1, got {errors}")


def test_partial_pydantic_follows_the_extra_setting_of_the_model():
    """Unknown keys are rejected with extra='forbid', dropped by default and kept with extra='allow'."""
    forbidden = _partial_errors({"bogus": 1}, schema=Closed)
    dropped = Validator().validate({"bogus": 1}, Member, partial=True)
    kept = Validator().validate({"bogus": 1}, Open, partial=True)

    if forbidden != {"bogus": "extra_forbidden"}:
        raise AssertionError(f"Expected 'bogus' to be forbidden, got {forbidden}")

    if dropped != {}:
        raise AssertionError(f"Expected an unknown key to be dropped, got {dropped!r}")

    if kept != {"bogus": 1}:
        raise AssertionError(f"Expected an unknown key to be kept, got {kept!r}")


def test_partial_pydantic_does_not_validate_defaults_of_unsent_fields():
    """With validate_default=True, a required field the body does not send is still not required."""
    result = Validator().validate({"label": "x"}, Closed, partial=True)

    if result != {"label": "x"}:
        raise AssertionError(f"Expected {{'label': 'x'}}, got {result!r}")


def test_partial_pydantic_skips_model_validators():
    """Model validators check a whole member, so they do not run on a partial body."""
    result = Validator().validate({"age": 12}, Member, partial=True)

    if result != {"age": 12}:
        raise AssertionError(f"Expected the partial body to pass without model validators, got {result!r}")


def test_full_pydantic_validation_is_unchanged():
    """A full body still returns a model instance and runs the model validators; the model itself is untouched."""
    validator = Validator()
    Validator().validate({"age": 1}, Member, partial=True)

    member = validator.validate({"name": "Ada", "age": 36, "email": "ada@example.com"}, Member)
    errors = {}
    try:
        validator.validate({"name": "Bo", "age": 12, "email": "bo@example.com"}, Member)
    except ValidationError as error:
        errors = {field_error.field: field_error.code for field_error in error.field_errors}

    if not isinstance(member, Member) or member.age != 36:
        raise AssertionError(f"Expected a Member instance, got {member!r}")

    if errors != {"$": "value_error"}:
        raise AssertionError(f"Expected the after model validator's error, got {errors}")

    if Member.model_fields["name"].is_required() is not True:
        raise AssertionError("Deriving the partial model must not change the original model")


# =============================================================================
# PATCH through the REST middleware
# =============================================================================

def _member_descriptor():
    """A descriptor declared through RestEndpoint.attach_at with a Pydantic request schema."""
    @RestEndpoint.attach_at(leaf="members", methods=["POST", "PATCH"], request_schema=Member)
    def change_member(request):
        return {}

    registry = EndpointRegistry()
    registry.collect_from(change_member)
    return registry.collect()[0]


def _patch(body) -> Request:
    """A PATCH request carrying ``body`` as JSON."""
    return Request("PATCH", "/members", headers={"Content-Type": "application/json"},
                   body=json.dumps(body).encode("utf-8"))


def test_middleware_patch_rejects_an_invalid_pydantic_body():
    """A PATCH body with a wrong type is answered with 400 and field errors; the handler is not called."""
    middleware = create_rest_middleware()
    calls = []

    def handler(request):
        calls.append(request)
        return {}

    response = middleware.process(_patch({"age": "abc"}), handler, descriptor=_member_descriptor())
    body = json.loads(response.body)

    if response.status_code != 400 or body["error"] != "validation_error":
        raise AssertionError(f"Expected 400 validation_error, got {response.status_code} {body}")

    fields = [field_error["field"] for field_error in body["field_errors"]]
    if fields != ["age"]:
        raise AssertionError(f"Expected a field error for 'age', got {fields}")

    if len(calls) != 0:
        raise AssertionError("The handler must not be called for an invalid body")


def test_middleware_patch_passes_the_sent_pydantic_fields_as_a_dict():
    """A valid PATCH body reaches the handler as a dict of the sent fields, like a dataclass schema's."""
    middleware = create_rest_middleware()
    received = []

    def handler(request):
        received.append(get_rest_payload(request))
        return {}

    response = middleware.process(_patch({"age": 40}), handler, descriptor=_member_descriptor())

    if response.status_code != 200:
        raise AssertionError(f"Expected 200, got {response.status_code}: {response.body!r}")

    if received != [{"age": 40}]:
        raise AssertionError(f"Expected the payload {{'age': 40}}, got {received!r}")
