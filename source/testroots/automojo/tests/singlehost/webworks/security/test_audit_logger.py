"""
    Tests for the audit logging components.

    This module contains unit tests for the AuditLevel enum, the Audit_Entry
    dataclass, the AuditDestination protocol, and the Audit_Logger class
    including log_authentication(), log_authorization(), log_violation(),
    add_destination(), and query().
"""

import json

from datetime import datetime, timedelta

from automojo.webworks.security.accesspolicy import AccessPolicy
from automojo.webworks.security.securitycontext import SecurityContext
from automojo.webworks.security.auditlogger import (
    AuditLevel,
    AuditEntry,
    AuditDestination,
    AuditLogger,
)
from automojo.testbase.mocking import Mock


# =============================================================================
# Unit Tests for AuditLevel
# =============================================================================

def test_audit_level_none_value():
    """
        Test that AuditLevel.NONE has the expected string value.
    """
    if AuditLevel.NONE.value != "none":
        errmsg = "Expected AuditLevel.NONE.value to be 'none', got '{}'".format(
            AuditLevel.NONE.value
        )
        raise AssertionError(errmsg)

    return


def test_audit_level_failures_only_value():
    """
        Test that AuditLevel.FAILURES_ONLY has the expected string value.
    """
    if AuditLevel.FAILURES_ONLY.value != "failures_only":
        errmsg = "Expected AuditLevel.FAILURES_ONLY.value to be 'failures_only', got '{}'".format(
            AuditLevel.FAILURES_ONLY.value
        )
        raise AssertionError(errmsg)

    return


def test_audit_level_all_value():
    """
        Test that AuditLevel.ALL has the expected string value.
    """
    if AuditLevel.ALL.value != "all":
        errmsg = "Expected AuditLevel.ALL.value to be 'all', got '{}'".format(
            AuditLevel.ALL.value
        )
        raise AssertionError(errmsg)

    return



def test_audit_level_has_three_members():
    """
        Test that AuditLevel has exactly three members.
    """
    members = list(AuditLevel)
    member_count = len(members)

    if member_count != 3:
        errmsg = "Expected AuditLevel to have 3 members, got {}".format(member_count)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Audit_Entry
# =============================================================================

def test_audit_entry_creation_with_all_fields():
    """
        Test that Audit_Entry can be created with all fields populated.
    """
    now = datetime.utcnow()

    entry = AuditEntry(
        timestamp=now,
        event_type="authentication",
        outcome="success",
        user_id="user-1",
        endpoint="/api/data",
        policy="roles=('admin',)",
        reason=None,
        ip_address="192.168.1.1",
        user_agent="TestAgent/1.0",
        request_id="req-001",
        correlation_id="corr-001",
        extra={"provider": "jwt"}
    )

    if entry.timestamp is not now:
        errmsg = "Expected timestamp to match"
        raise AssertionError(errmsg)

    if entry.event_type != "authentication":
        errmsg = "Expected event_type 'authentication', got '{}'".format(entry.event_type)
        raise AssertionError(errmsg)

    if entry.outcome != "success":
        errmsg = "Expected outcome 'success', got '{}'".format(entry.outcome)
        raise AssertionError(errmsg)

    if entry.user_id != "user-1":
        errmsg = "Expected user_id 'user-1', got '{}'".format(entry.user_id)
        raise AssertionError(errmsg)

    if entry.endpoint != "/api/data":
        errmsg = "Expected endpoint '/api/data', got '{}'".format(entry.endpoint)
        raise AssertionError(errmsg)

    if entry.ip_address != "192.168.1.1":
        errmsg = "Expected ip_address '192.168.1.1', got '{}'".format(entry.ip_address)
        raise AssertionError(errmsg)

    if entry.user_agent != "TestAgent/1.0":
        errmsg = "Expected user_agent 'TestAgent/1.0', got '{}'".format(entry.user_agent)
        raise AssertionError(errmsg)

    if entry.request_id != "req-001":
        errmsg = "Expected request_id 'req-001', got '{}'".format(entry.request_id)
        raise AssertionError(errmsg)

    if entry.correlation_id != "corr-001":
        errmsg = "Expected correlation_id 'corr-001', got '{}'".format(entry.correlation_id)
        raise AssertionError(errmsg)

    return


def test_audit_entry_extra_defaults_to_empty_dict():
    """
        Test that the extra field defaults to an empty dictionary when
        not provided.
    """
    now = datetime.utcnow()

    entry = AuditEntry(
        timestamp=now,
        event_type="authorization",
        outcome="failure",
        user_id=None,
        endpoint=None,
        policy=None,
        reason="Access denied",
        ip_address=None,
        user_agent=None,
        request_id=None,
        correlation_id=None,
    )

    if not isinstance(entry.extra, dict):
        errmsg = "Expected extra to be a dict, got {}".format(type(entry.extra))
        raise AssertionError(errmsg)

    if len(entry.extra) != 0:
        errmsg = "Expected extra to be empty, got {}".format(entry.extra)
        raise AssertionError(errmsg)

    return


def test_audit_entry_to_json_produces_valid_json():
    """
        Test that to_json() produces a valid JSON string that can be
        parsed back into a dictionary.
    """
    now = datetime.utcnow()

    entry = AuditEntry(
        timestamp=now,
        event_type="authentication",
        outcome="success",
        user_id="user-1",
        endpoint="/api/data",
        policy=None,
        reason=None,
        ip_address="10.0.0.1",
        user_agent="Agent/2.0",
        request_id="req-100",
        correlation_id="corr-200",
        extra={"provider": "session"}
    )

    json_str = entry.to_json()

    parsed = json.loads(json_str)

    if parsed["event_type"] != "authentication":
        errmsg = "Expected event_type 'authentication' in JSON, got '{}'".format(
            parsed["event_type"]
        )
        raise AssertionError(errmsg)

    if parsed["outcome"] != "success":
        errmsg = "Expected outcome 'success' in JSON, got '{}'".format(parsed["outcome"])
        raise AssertionError(errmsg)

    if parsed["user_id"] != "user-1":
        errmsg = "Expected user_id 'user-1' in JSON, got '{}'".format(parsed["user_id"])
        raise AssertionError(errmsg)

    if parsed["timestamp"] != now.isoformat():
        errmsg = "Expected timestamp '{}' in JSON, got '{}'".format(
            now.isoformat(), parsed["timestamp"]
        )
        raise AssertionError(errmsg)

    return


def test_audit_entry_to_json_includes_all_fields():
    """
        Test that to_json() includes all expected fields in the output.
    """
    now = datetime.utcnow()

    entry = AuditEntry(
        timestamp=now,
        event_type="violation",
        outcome="failure",
        user_id="user-2",
        endpoint="/admin",
        policy="require_auth=True",
        reason="Missing required role",
        ip_address="172.16.0.1",
        user_agent="Bot/1.0",
        request_id="req-999",
        correlation_id=None,
        extra={"detail": "attempted admin access"}
    )

    json_str = entry.to_json()
    parsed = json.loads(json_str)

    expected_keys = [
        "timestamp", "event_type", "outcome", "user_id", "endpoint",
        "policy", "reason", "ip_address", "user_agent", "request_id",
        "correlation_id", "extra"
    ]

    for key in expected_keys:
        if key not in parsed:
            errmsg = "Expected key '{}' in JSON output, but it was missing".format(key)
            raise AssertionError(errmsg)

    return



def test_audit_entry_as_dict_returns_dictionary():
    """
        Test that as_dict() returns a dictionary with all entry fields.
    """
    now = datetime.utcnow()

    entry = AuditEntry(
        timestamp=now,
        event_type="authentication",
        outcome="success",
        user_id="user-1",
        endpoint="/api",
        policy=None,
        reason=None,
        ip_address="10.0.0.1",
        user_agent="Agent/1.0",
        request_id="req-1",
        correlation_id=None,
    )

    result = entry.as_dict()

    if not isinstance(result, dict):
        errmsg = "Expected as_dict() to return a dict, got {}".format(type(result))
        raise AssertionError(errmsg)

    if result["event_type"] != "authentication":
        errmsg = "Expected event_type 'authentication', got '{}'".format(result["event_type"])
        raise AssertionError(errmsg)

    if result["timestamp"] != now.isoformat():
        errmsg = "Expected timestamp as ISO string"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for AuditDestination
# =============================================================================

def test_audit_destination_write_can_be_called():
    """
        Test that AuditDestination can be instantiated and its write
        method can be called.
    """
    dest = AuditDestination()
    now = datetime.utcnow()

    entry = AuditEntry(
        timestamp=now,
        event_type="authentication",
        outcome="success",
        user_id="user-1",
        endpoint="/api",
        policy=None,
        reason=None,
        ip_address=None,
        user_agent=None,
        request_id=None,
        correlation_id=None,
    )

    # Should not raise
    dest.write(entry)

    return


# =============================================================================
# Unit Tests for Audit_Logger - Initialization
# =============================================================================

def test_logger_default_level_is_all():
    """
        Test that Audit_Logger defaults to AuditLevel.ALL.
    """
    logger = AuditLogger()

    if logger._level != AuditLevel.ALL:
        errmsg = "Expected default level AuditLevel.ALL, got {}".format(logger._level)
        raise AssertionError(errmsg)

    return


def test_logger_default_destinations_is_empty():
    """
        Test that Audit_Logger defaults to an empty destinations list.
    """
    logger = AuditLogger()

    if len(logger._destinations) != 0:
        errmsg = "Expected empty destinations list, got {} items".format(
            len(logger._destinations)
        )
        raise AssertionError(errmsg)

    return


def test_logger_accepts_custom_level():
    """
        Test that Audit_Logger accepts a custom audit level.
    """
    logger = AuditLogger(level=AuditLevel.FAILURES_ONLY)

    if logger._level != AuditLevel.FAILURES_ONLY:
        errmsg = "Expected level FAILURES_ONLY, got {}".format(logger._level)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Audit_Logger - log_authentication()
# =============================================================================

def test_log_authentication_success():
    """
        Test that log_authentication creates an entry for a successful
        authentication attempt.
    """
    logger = AuditLogger()
    ctx = SecurityContext(user_id="user-1", provider="jwt")

    logger.log_authentication(
        context=ctx,
        provider="jwt",
        success=True,
        endpoint="/api/data",
        ip_address="10.0.0.1",
        user_agent="Agent/1.0",
        request_id="req-1",
    )

    entries = logger.query()

    if len(entries) != 1:
        errmsg = "Expected 1 entry, got {}".format(len(entries))
        raise AssertionError(errmsg)

    entry = entries[0]

    if entry.event_type != "authentication":
        errmsg = "Expected event_type 'authentication', got '{}'".format(entry.event_type)
        raise AssertionError(errmsg)

    if entry.outcome != "success":
        errmsg = "Expected outcome 'success', got '{}'".format(entry.outcome)
        raise AssertionError(errmsg)

    if entry.user_id != "user-1":
        errmsg = "Expected user_id 'user-1', got '{}'".format(entry.user_id)
        raise AssertionError(errmsg)

    return


def test_log_authentication_failure():
    """
        Test that log_authentication creates an entry for a failed
        authentication attempt.
    """
    logger = AuditLogger()
    ctx = SecurityContext.guest()

    logger.log_authentication(
        context=ctx,
        provider="jwt",
        success=False,
        endpoint="/api/data",
    )

    entries = logger.query()

    if len(entries) != 1:
        errmsg = "Expected 1 entry, got {}".format(len(entries))
        raise AssertionError(errmsg)

    entry = entries[0]

    if entry.outcome != "failure":
        errmsg = "Expected outcome 'failure', got '{}'".format(entry.outcome)
        raise AssertionError(errmsg)

    if entry.user_id is not None:
        errmsg = "Expected user_id None for guest, got '{}'".format(entry.user_id)
        raise AssertionError(errmsg)

    return


def test_log_authentication_dispatches_to_destination():
    """
        Test that log_authentication writes the entry to registered
        destinations.
    """
    mock_dest = Mock()
    mock_dest.configure(recursive=True)

    written_entries = []

    def capture_write(entry):
        written_entries.append(entry)

    mock_dest.mock_context().mock_method("write", side_effect=capture_write)

    logger = AuditLogger(destinations=[mock_dest])
    ctx = SecurityContext(user_id="user-1")

    logger.log_authentication(
        context=ctx,
        provider="session",
        success=True,
    )

    if len(written_entries) != 1:
        errmsg = "Expected destination to receive 1 entry, got {}".format(
            len(written_entries)
        )
        raise AssertionError(errmsg)

    return



# =============================================================================
# Unit Tests for Audit_Logger - log_authorization()
# =============================================================================

def test_log_authorization_success():
    """
        Test that log_authorization creates an entry for a successful
        authorization decision.
    """
    logger = AuditLogger()
    ctx = SecurityContext(user_id="user-1", roles=("admin",))
    policy = AccessPolicy(roles=("admin",))

    logger.log_authorization(
        context=ctx,
        policy=policy,
        allowed=True,
        endpoint="/admin/dashboard",
    )

    entries = logger.query()

    if len(entries) != 1:
        errmsg = "Expected 1 entry, got {}".format(len(entries))
        raise AssertionError(errmsg)

    entry = entries[0]

    if entry.event_type != "authorization":
        errmsg = "Expected event_type 'authorization', got '{}'".format(entry.event_type)
        raise AssertionError(errmsg)

    if entry.outcome != "success":
        errmsg = "Expected outcome 'success', got '{}'".format(entry.outcome)
        raise AssertionError(errmsg)

    if entry.policy is None:
        errmsg = "Expected policy to be set in the entry"
        raise AssertionError(errmsg)

    return


def test_log_authorization_failure():
    """
        Test that log_authorization creates an entry for a failed
        authorization decision.
    """
    logger = AuditLogger()
    ctx = SecurityContext(user_id="user-1", roles=("viewer",))
    policy = AccessPolicy(roles=("admin",))

    logger.log_authorization(
        context=ctx,
        policy=policy,
        allowed=False,
        reason="Missing required role",
        endpoint="/admin/dashboard",
    )

    entries = logger.query()

    if len(entries) != 1:
        errmsg = "Expected 1 entry, got {}".format(len(entries))
        raise AssertionError(errmsg)

    entry = entries[0]

    if entry.outcome != "failure":
        errmsg = "Expected outcome 'failure', got '{}'".format(entry.outcome)
        raise AssertionError(errmsg)

    if entry.reason != "Missing required role":
        errmsg = "Expected reason 'Missing required role', got '{}'".format(entry.reason)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Audit_Logger - log_violation()
# =============================================================================

def test_log_violation_creates_failure_entry():
    """
        Test that log_violation creates an entry with outcome 'failure'
        and event_type 'violation'.
    """
    logger = AuditLogger()
    ctx = SecurityContext(user_id="user-1")
    policy = AccessPolicy(roles=("admin",), scopes=("write",))

    logger.log_violation(
        context=ctx,
        policy=policy,
        constraint="Missing required role: admin",
        endpoint="/admin/settings",
        ip_address="192.168.1.100",
    )

    entries = logger.query()

    if len(entries) != 1:
        errmsg = "Expected 1 entry, got {}".format(len(entries))
        raise AssertionError(errmsg)

    entry = entries[0]

    if entry.event_type != "violation":
        errmsg = "Expected event_type 'violation', got '{}'".format(entry.event_type)
        raise AssertionError(errmsg)

    if entry.outcome != "failure":
        errmsg = "Expected outcome 'failure', got '{}'".format(entry.outcome)
        raise AssertionError(errmsg)

    if entry.reason != "Missing required role: admin":
        errmsg = "Expected reason to contain constraint, got '{}'".format(entry.reason)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Audit_Logger - AuditLevel filtering
# =============================================================================

def test_level_none_logs_nothing():
    """
        Test that AuditLevel.NONE prevents all events from being logged.
    """
    logger = AuditLogger(level=AuditLevel.NONE)
    ctx = SecurityContext(user_id="user-1")

    logger.log_authentication(context=ctx, provider="jwt", success=True)
    logger.log_authentication(context=ctx, provider="jwt", success=False)

    entries = logger.query()

    if len(entries) != 0:
        errmsg = "Expected 0 entries with NONE level, got {}".format(len(entries))
        raise AssertionError(errmsg)

    return


def test_level_failures_only_logs_only_failures():
    """
        Test that AuditLevel.FAILURES_ONLY logs only failed events.
    """
    logger = AuditLogger(level=AuditLevel.FAILURES_ONLY)
    ctx = SecurityContext(user_id="user-1")

    logger.log_authentication(context=ctx, provider="jwt", success=True)
    logger.log_authentication(context=ctx, provider="jwt", success=False)

    entries = logger.query()

    if len(entries) != 1:
        errmsg = "Expected 1 entry with FAILURES_ONLY level, got {}".format(len(entries))
        raise AssertionError(errmsg)

    if entries[0].outcome != "failure":
        errmsg = "Expected only failure entries, got '{}'".format(entries[0].outcome)
        raise AssertionError(errmsg)

    return


def test_level_all_logs_everything():
    """
        Test that AuditLevel.ALL logs both successes and failures.
    """
    logger = AuditLogger(level=AuditLevel.ALL)
    ctx = SecurityContext(user_id="user-1")

    logger.log_authentication(context=ctx, provider="jwt", success=True)
    logger.log_authentication(context=ctx, provider="jwt", success=False)

    entries = logger.query()

    if len(entries) != 2:
        errmsg = "Expected 2 entries with ALL level, got {}".format(len(entries))
        raise AssertionError(errmsg)

    return


def test_level_failures_only_logs_violations():
    """
        Test that AuditLevel.FAILURES_ONLY logs violations since they
        are always failures.
    """
    logger = AuditLogger(level=AuditLevel.FAILURES_ONLY)
    ctx = SecurityContext(user_id="user-1")
    policy = AccessPolicy(roles=("admin",))

    logger.log_violation(
        context=ctx,
        policy=policy,
        constraint="Missing required role",
    )

    entries = logger.query()

    if len(entries) != 1:
        errmsg = "Expected 1 violation entry, got {}".format(len(entries))
        raise AssertionError(errmsg)

    return


def test_level_none_blocks_violations():
    """
        Test that AuditLevel.NONE blocks even violation events.
    """
    logger = AuditLogger(level=AuditLevel.NONE)
    ctx = SecurityContext(user_id="user-1")
    policy = AccessPolicy(roles=("admin",))

    logger.log_violation(
        context=ctx,
        policy=policy,
        constraint="Missing required role",
    )

    entries = logger.query()

    if len(entries) != 0:
        errmsg = "Expected 0 entries with NONE level, got {}".format(len(entries))
        raise AssertionError(errmsg)

    return



# =============================================================================
# Unit Tests for Audit_Logger - add_destination()
# =============================================================================

def test_add_destination_increases_destination_count():
    """
        Test that add_destination adds a destination to the logger.
    """
    logger = AuditLogger()

    mock_dest = Mock()
    mock_dest.configure(recursive=True)

    logger.add_destination(mock_dest)

    if len(logger._destinations) != 1:
        errmsg = "Expected 1 destination, got {}".format(len(logger._destinations))
        raise AssertionError(errmsg)

    return


def test_add_multiple_destinations():
    """
        Test that multiple destinations can be added and all receive entries.
    """
    written_a = []
    written_b = []

    mock_a = Mock()
    mock_a.configure(recursive=True)
    mock_a.mock_context().mock_method("write", side_effect=lambda e: written_a.append(e))

    mock_b = Mock()
    mock_b.configure(recursive=True)
    mock_b.mock_context().mock_method("write", side_effect=lambda e: written_b.append(e))

    logger = AuditLogger()
    logger.add_destination(mock_a)
    logger.add_destination(mock_b)

    ctx = SecurityContext(user_id="user-1")
    logger.log_authentication(context=ctx, provider="jwt", success=True)

    if len(written_a) != 1:
        errmsg = "Expected destination A to receive 1 entry, got {}".format(len(written_a))
        raise AssertionError(errmsg)

    if len(written_b) != 1:
        errmsg = "Expected destination B to receive 1 entry, got {}".format(len(written_b))
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Audit_Logger - query()
# =============================================================================

def test_query_returns_all_entries_with_no_filters():
    """
        Test that query() returns all entries when no filters are provided.
    """
    logger = AuditLogger()
    ctx = SecurityContext(user_id="user-1")

    logger.log_authentication(context=ctx, provider="jwt", success=True)
    logger.log_authentication(context=ctx, provider="jwt", success=False)

    results = logger.query()

    if len(results) != 2:
        errmsg = "Expected 2 entries, got {}".format(len(results))
        raise AssertionError(errmsg)

    return


def test_query_filters_by_event_type():
    """
        Test that query() filters entries by event_type.
    """
    logger = AuditLogger()
    ctx = SecurityContext(user_id="user-1")
    policy = AccessPolicy(roles=("admin",))

    logger.log_authentication(context=ctx, provider="jwt", success=True)
    logger.log_authorization(context=ctx, policy=policy, allowed=True)

    auth_results = logger.query(event_type="authentication")

    if len(auth_results) != 1:
        errmsg = "Expected 1 authentication entry, got {}".format(len(auth_results))
        raise AssertionError(errmsg)

    if auth_results[0].event_type != "authentication":
        errmsg = "Expected event_type 'authentication', got '{}'".format(
            auth_results[0].event_type
        )
        raise AssertionError(errmsg)

    return


def test_query_filters_by_user_id():
    """
        Test that query() filters entries by user_id.
    """
    logger = AuditLogger()
    ctx_a = SecurityContext(user_id="user-a")
    ctx_b = SecurityContext(user_id="user-b")

    logger.log_authentication(context=ctx_a, provider="jwt", success=True)
    logger.log_authentication(context=ctx_b, provider="jwt", success=True)

    results = logger.query(user_id="user-a")

    if len(results) != 1:
        errmsg = "Expected 1 entry for user-a, got {}".format(len(results))
        raise AssertionError(errmsg)

    if results[0].user_id != "user-a":
        errmsg = "Expected user_id 'user-a', got '{}'".format(results[0].user_id)
        raise AssertionError(errmsg)

    return


def test_query_filters_by_outcome():
    """
        Test that query() filters entries by outcome.
    """
    logger = AuditLogger()
    ctx = SecurityContext(user_id="user-1")

    logger.log_authentication(context=ctx, provider="jwt", success=True)
    logger.log_authentication(context=ctx, provider="jwt", success=False)

    failure_results = logger.query(outcome="failure")

    if len(failure_results) != 1:
        errmsg = "Expected 1 failure entry, got {}".format(len(failure_results))
        raise AssertionError(errmsg)

    if failure_results[0].outcome != "failure":
        errmsg = "Expected outcome 'failure', got '{}'".format(failure_results[0].outcome)
        raise AssertionError(errmsg)

    return


def test_query_filters_by_time_range():
    """
        Test that query() filters entries by start_time and end_time.
    """
    logger = AuditLogger()
    ctx = SecurityContext(user_id="user-1")

    # Log three entries
    logger.log_authentication(context=ctx, provider="jwt", success=True)
    logger.log_authentication(context=ctx, provider="jwt", success=True)
    logger.log_authentication(context=ctx, provider="jwt", success=True)

    all_entries = logger.query()

    if len(all_entries) != 3:
        errmsg = "Expected 3 entries, got {}".format(len(all_entries))
        raise AssertionError(errmsg)

    # Query with a future start_time should return nothing
    future_time = datetime.utcnow() + timedelta(hours=1)
    future_results = logger.query(start_time=future_time)

    if len(future_results) != 0:
        errmsg = "Expected 0 entries with future start_time, got {}".format(
            len(future_results)
        )
        raise AssertionError(errmsg)

    # Query with a past end_time should return nothing
    past_time = datetime.utcnow() - timedelta(hours=1)
    past_results = logger.query(end_time=past_time)

    if len(past_results) != 0:
        errmsg = "Expected 0 entries with past end_time, got {}".format(
            len(past_results)
        )
        raise AssertionError(errmsg)

    return


def test_query_combines_multiple_filters():
    """
        Test that query() combines multiple filters with AND logic.
    """
    logger = AuditLogger()
    ctx_a = SecurityContext(user_id="user-a")
    ctx_b = SecurityContext(user_id="user-b")

    logger.log_authentication(context=ctx_a, provider="jwt", success=True)
    logger.log_authentication(context=ctx_a, provider="jwt", success=False)
    logger.log_authentication(context=ctx_b, provider="jwt", success=False)

    results = logger.query(user_id="user-a", outcome="failure")

    if len(results) != 1:
        errmsg = "Expected 1 entry matching both filters, got {}".format(len(results))
        raise AssertionError(errmsg)

    if results[0].user_id != "user-a":
        errmsg = "Expected user_id 'user-a', got '{}'".format(results[0].user_id)
        raise AssertionError(errmsg)

    if results[0].outcome != "failure":
        errmsg = "Expected outcome 'failure', got '{}'".format(results[0].outcome)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property-Based Tests for Audit Log Completeness
# **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.7**
# =============================================================================

import random
import string


def _random_string(min_length=1, max_length=12):
    """
        Generate a random lowercase string.

        :param min_length: Minimum length of the string.
        :param max_length: Maximum length of the string.

        :returns: A random lowercase string.
    """
    length = random.randint(min_length, max_length)
    rtnval = "".join(random.choices(string.ascii_lowercase, k=length))
    return rtnval


def _random_string_tuple(max_length=4):
    """
        Generate a tuple of random unique strings.

        :param max_length: Maximum number of items in the tuple.

        :returns: A tuple of unique random strings.
    """
    count = random.randint(0, max_length)
    seen = set()
    items = []
    for _ in range(count):
        item = _random_string()
        if item not in seen:
            seen.add(item)
            items.append(item)

    rtnval = tuple(items)
    return rtnval


def _random_ip_address():
    """
        Generate a random IPv4 address string.

        :returns: A string in dotted-quad notation.
    """
    octets = [str(random.randint(0, 255)) for _ in range(4)]
    rtnval = ".".join(octets)
    return rtnval


def _random_user_agent():
    """
        Generate a random user agent string.

        :returns: A user agent string like 'AgentName/Version'.
    """
    name = _random_string(3, 8).capitalize()
    major = random.randint(1, 10)
    minor = random.randint(0, 9)
    rtnval = "{}/{}.{}".format(name, major, minor)
    return rtnval


def _random_request_id():
    """
        Generate a random request identifier.

        :returns: A string like 'req-xxxxxxxx'.
    """
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    rtnval = "req-{}".format(suffix)
    return rtnval


def _random_security_context():
    """
        Generate a random Security_Context. Approximately half will be
        authenticated (have a user_id) and half will be guests.

        :returns: A randomly configured Security_Context instance.
    """
    is_authenticated = random.choice([True, False])

    if is_authenticated:
        user_id = "user-" + _random_string(3, 6)
    else:
        user_id = None

    roles = _random_string_tuple()
    scopes = _random_string_tuple()

    rtnval = SecurityContext(
        user_id=user_id,
        roles=roles,
        scopes=scopes,
    )
    return rtnval


def _random_access_policy():
    """
        Generate a random AccessPolicy with random roles, scopes, and
        require_auth setting.

        :returns: A randomly configured AccessPolicy instance.
    """
    roles = _random_string_tuple()
    scopes = _random_string_tuple()
    require_auth = random.choice([True, False])

    rtnval = AccessPolicy(
        roles=roles,
        scopes=scopes,
        require_auth=require_auth,
    )
    return rtnval


def test_property_audit_log_completeness_authentication():
    """
        Property test for Audit Log Completeness on authentication events.

        **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.7**

        For any authentication attempt:
        - An Audit_Entry SHALL be created with timestamp, event_type, and outcome
        - The entry SHALL include user_id (if authenticated), endpoint, and policy
        - The entry SHALL include request metadata: IP address, user agent, request_id
        - The entry SHALL be serializable to valid JSON
    """
    iteration_count = 100

    for iteration in range(iteration_count):
        logger = AuditLogger(level=AuditLevel.ALL)
        ctx = _random_security_context()
        provider_name = _random_string(3, 8)
        success = random.choice([True, False])
        endpoint = "/" + _random_string(3, 10)
        ip_address = _random_ip_address()
        user_agent = _random_user_agent()
        request_id = _random_request_id()

        logger.log_authentication(
            context=ctx,
            provider=provider_name,
            success=success,
            endpoint=endpoint,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

        entries = logger.query()

        if len(entries) != 1:
            errmsg = (
                "Iteration {}: Expected 1 entry, got {}".format(iteration, len(entries))
            )
            raise AssertionError(errmsg)

        entry = entries[0]

        # --- Verify timestamp is present ---
        if entry.timestamp is None:
            errmsg = "Iteration {}: Entry timestamp is None".format(iteration)
            raise AssertionError(errmsg)

        if not isinstance(entry.timestamp, datetime):
            errmsg = (
                "Iteration {}: Expected timestamp to be datetime, got {}".format(
                    iteration, type(entry.timestamp)
                )
            )
            raise AssertionError(errmsg)

        # --- Verify event_type ---
        if entry.event_type != "authentication":
            errmsg = (
                "Iteration {}: Expected event_type 'authentication', got '{}'".format(
                    iteration, entry.event_type
                )
            )
            raise AssertionError(errmsg)

        # --- Verify outcome ---
        expected_outcome = "success" if success else "failure"
        if entry.outcome != expected_outcome:
            errmsg = (
                "Iteration {}: Expected outcome '{}', got '{}'".format(
                    iteration, expected_outcome, entry.outcome
                )
            )
            raise AssertionError(errmsg)

        # --- Verify user_id matches context ---
        if entry.user_id != ctx.user_id:
            errmsg = (
                "Iteration {}: Expected user_id '{}', got '{}'".format(
                    iteration, ctx.user_id, entry.user_id
                )
            )
            raise AssertionError(errmsg)

        # --- Verify endpoint ---
        if entry.endpoint != endpoint:
            errmsg = (
                "Iteration {}: Expected endpoint '{}', got '{}'".format(
                    iteration, endpoint, entry.endpoint
                )
            )
            raise AssertionError(errmsg)

        # --- Verify request metadata ---
        if entry.ip_address != ip_address:
            errmsg = (
                "Iteration {}: Expected ip_address '{}', got '{}'".format(
                    iteration, ip_address, entry.ip_address
                )
            )
            raise AssertionError(errmsg)

        if entry.user_agent != user_agent:
            errmsg = (
                "Iteration {}: Expected user_agent '{}', got '{}'".format(
                    iteration, user_agent, entry.user_agent
                )
            )
            raise AssertionError(errmsg)

        if entry.request_id != request_id:
            errmsg = (
                "Iteration {}: Expected request_id '{}', got '{}'".format(
                    iteration, request_id, entry.request_id
                )
            )
            raise AssertionError(errmsg)

        # --- Verify JSON serialization ---
        json_str = entry.to_json()
        parsed = json.loads(json_str)

        if not isinstance(parsed, dict):
            errmsg = (
                "Iteration {}: Expected JSON to parse to dict, got {}".format(
                    iteration, type(parsed)
                )
            )
            raise AssertionError(errmsg)

        required_keys = [
            "timestamp", "event_type", "outcome", "user_id",
            "endpoint", "ip_address", "user_agent", "request_id",
        ]
        for key in required_keys:
            if key not in parsed:
                errmsg = (
                    "Iteration {}: Missing key '{}' in JSON output".format(
                        iteration, key
                    )
                )
                raise AssertionError(errmsg)

    return


def test_property_audit_log_completeness_authorization():
    """
        Property test for Audit Log Completeness on authorization events.

        **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.7**

        For any authorization decision:
        - An Audit_Entry SHALL be created with timestamp, event_type, and outcome
        - The entry SHALL include user_id (if authenticated), endpoint, and policy
        - The entry SHALL include request metadata: IP address, user agent, request_id
        - The entry SHALL be serializable to valid JSON
    """
    iteration_count = 100

    for iteration in range(iteration_count):
        logger = AuditLogger(level=AuditLevel.ALL)
        ctx = _random_security_context()
        policy = _random_access_policy()
        allowed = random.choice([True, False])
        reason = _random_string(5, 20) if not allowed else None
        endpoint = "/" + _random_string(3, 10)
        ip_address = _random_ip_address()
        user_agent = _random_user_agent()
        request_id = _random_request_id()

        logger.log_authorization(
            context=ctx,
            policy=policy,
            allowed=allowed,
            reason=reason,
            endpoint=endpoint,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

        entries = logger.query()

        if len(entries) != 1:
            errmsg = (
                "Iteration {}: Expected 1 entry, got {}".format(iteration, len(entries))
            )
            raise AssertionError(errmsg)

        entry = entries[0]

        # --- Verify timestamp is present ---
        if entry.timestamp is None:
            errmsg = "Iteration {}: Entry timestamp is None".format(iteration)
            raise AssertionError(errmsg)

        if not isinstance(entry.timestamp, datetime):
            errmsg = (
                "Iteration {}: Expected timestamp to be datetime, got {}".format(
                    iteration, type(entry.timestamp)
                )
            )
            raise AssertionError(errmsg)

        # --- Verify event_type ---
        if entry.event_type != "authorization":
            errmsg = (
                "Iteration {}: Expected event_type 'authorization', got '{}'".format(
                    iteration, entry.event_type
                )
            )
            raise AssertionError(errmsg)

        # --- Verify outcome ---
        expected_outcome = "success" if allowed else "failure"
        if entry.outcome != expected_outcome:
            errmsg = (
                "Iteration {}: Expected outcome '{}', got '{}'".format(
                    iteration, expected_outcome, entry.outcome
                )
            )
            raise AssertionError(errmsg)

        # --- Verify user_id matches context ---
        if entry.user_id != ctx.user_id:
            errmsg = (
                "Iteration {}: Expected user_id '{}', got '{}'".format(
                    iteration, ctx.user_id, entry.user_id
                )
            )
            raise AssertionError(errmsg)

        # --- Verify endpoint ---
        if entry.endpoint != endpoint:
            errmsg = (
                "Iteration {}: Expected endpoint '{}', got '{}'".format(
                    iteration, endpoint, entry.endpoint
                )
            )
            raise AssertionError(errmsg)

        # --- Verify policy is recorded ---
        if entry.policy is None:
            errmsg = (
                "Iteration {}: Expected policy to be set, got None".format(iteration)
            )
            raise AssertionError(errmsg)

        # --- Verify request metadata ---
        if entry.ip_address != ip_address:
            errmsg = (
                "Iteration {}: Expected ip_address '{}', got '{}'".format(
                    iteration, ip_address, entry.ip_address
                )
            )
            raise AssertionError(errmsg)

        if entry.user_agent != user_agent:
            errmsg = (
                "Iteration {}: Expected user_agent '{}', got '{}'".format(
                    iteration, user_agent, entry.user_agent
                )
            )
            raise AssertionError(errmsg)

        if entry.request_id != request_id:
            errmsg = (
                "Iteration {}: Expected request_id '{}', got '{}'".format(
                    iteration, request_id, entry.request_id
                )
            )
            raise AssertionError(errmsg)

        # --- Verify JSON serialization ---
        json_str = entry.to_json()
        parsed = json.loads(json_str)

        if not isinstance(parsed, dict):
            errmsg = (
                "Iteration {}: Expected JSON to parse to dict, got {}".format(
                    iteration, type(parsed)
                )
            )
            raise AssertionError(errmsg)

        required_keys = [
            "timestamp", "event_type", "outcome", "user_id",
            "endpoint", "policy", "ip_address", "user_agent", "request_id",
        ]
        for key in required_keys:
            if key not in parsed:
                errmsg = (
                    "Iteration {}: Missing key '{}' in JSON output".format(
                        iteration, key
                    )
                )
                raise AssertionError(errmsg)

    return


def test_property_audit_log_completeness_violation():
    """
        Property test for Audit Log Completeness on violation events.

        **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.7**

        For any policy violation:
        - An Audit_Entry SHALL be created with timestamp, event_type, and outcome
        - The entry SHALL include user_id (if authenticated), endpoint, and policy
        - The entry SHALL include request metadata: IP address, user agent, request_id
        - The entry SHALL be serializable to valid JSON
    """
    iteration_count = 100

    for iteration in range(iteration_count):
        logger = AuditLogger(level=AuditLevel.ALL)
        ctx = _random_security_context()
        policy = _random_access_policy()
        constraint = _random_string(5, 30)
        endpoint = "/" + _random_string(3, 10)
        ip_address = _random_ip_address()
        user_agent = _random_user_agent()
        request_id = _random_request_id()

        logger.log_violation(
            context=ctx,
            policy=policy,
            constraint=constraint,
            endpoint=endpoint,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

        entries = logger.query()

        if len(entries) != 1:
            errmsg = (
                "Iteration {}: Expected 1 entry, got {}".format(iteration, len(entries))
            )
            raise AssertionError(errmsg)

        entry = entries[0]

        # --- Verify timestamp is present ---
        if entry.timestamp is None:
            errmsg = "Iteration {}: Entry timestamp is None".format(iteration)
            raise AssertionError(errmsg)

        if not isinstance(entry.timestamp, datetime):
            errmsg = (
                "Iteration {}: Expected timestamp to be datetime, got {}".format(
                    iteration, type(entry.timestamp)
                )
            )
            raise AssertionError(errmsg)

        # --- Verify event_type ---
        if entry.event_type != "violation":
            errmsg = (
                "Iteration {}: Expected event_type 'violation', got '{}'".format(
                    iteration, entry.event_type
                )
            )
            raise AssertionError(errmsg)

        # --- Verify outcome is always failure for violations ---
        if entry.outcome != "failure":
            errmsg = (
                "Iteration {}: Expected outcome 'failure' for violation, got '{}'".format(
                    iteration, entry.outcome
                )
            )
            raise AssertionError(errmsg)

        # --- Verify user_id matches context ---
        if entry.user_id != ctx.user_id:
            errmsg = (
                "Iteration {}: Expected user_id '{}', got '{}'".format(
                    iteration, ctx.user_id, entry.user_id
                )
            )
            raise AssertionError(errmsg)

        # --- Verify endpoint ---
        if entry.endpoint != endpoint:
            errmsg = (
                "Iteration {}: Expected endpoint '{}', got '{}'".format(
                    iteration, endpoint, entry.endpoint
                )
            )
            raise AssertionError(errmsg)

        # --- Verify policy is recorded ---
        if entry.policy is None:
            errmsg = (
                "Iteration {}: Expected policy to be set, got None".format(iteration)
            )
            raise AssertionError(errmsg)

        # --- Verify request metadata ---
        if entry.ip_address != ip_address:
            errmsg = (
                "Iteration {}: Expected ip_address '{}', got '{}'".format(
                    iteration, ip_address, entry.ip_address
                )
            )
            raise AssertionError(errmsg)

        if entry.user_agent != user_agent:
            errmsg = (
                "Iteration {}: Expected user_agent '{}', got '{}'".format(
                    iteration, user_agent, entry.user_agent
                )
            )
            raise AssertionError(errmsg)

        if entry.request_id != request_id:
            errmsg = (
                "Iteration {}: Expected request_id '{}', got '{}'".format(
                    iteration, request_id, entry.request_id
                )
            )
            raise AssertionError(errmsg)

        # --- Verify JSON serialization ---
        json_str = entry.to_json()
        parsed = json.loads(json_str)

        if not isinstance(parsed, dict):
            errmsg = (
                "Iteration {}: Expected JSON to parse to dict, got {}".format(
                    iteration, type(parsed)
                )
            )
            raise AssertionError(errmsg)

        required_keys = [
            "timestamp", "event_type", "outcome", "user_id",
            "endpoint", "policy", "ip_address", "user_agent", "request_id",
        ]
        for key in required_keys:
            if key not in parsed:
                errmsg = (
                    "Iteration {}: Missing key '{}' in JSON output".format(
                        iteration, key
                    )
                )
                raise AssertionError(errmsg)

    return
