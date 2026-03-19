"""
.. module:: auditlogger
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Audit logging for security events including authentication attempts,
        authorization decisions, and policy violations.

.. moduleauthor:: Automation Mojo LLC

This module provides the audit logging infrastructure for the security framework.
It includes the AuditLevel enum for configuring logging verbosity, the AuditEntry
dataclass for structured log entries, the AuditDestination protocol for pluggable
log destinations, and the AuditLogger class that coordinates logging of security
events.

The AuditLogger supports multiple destinations, configurable audit levels, and
provides a query interface for retrieving historical security events. Logging is
designed to avoid blocking request processing.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import json

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from automojo.webworks.security.accesspolicy import AccessPolicy
from automojo.webworks.security.securitycontext import SecurityContext


class AuditLevel(Enum):
    """
        Audit logging levels controlling which events are recorded.

        NONE disables all audit logging. FAILURES_ONLY records only
        failed authentication and authorization attempts. ALL records
        every security event regardless of outcome.
    """

    NONE = "none"
    FAILURES_ONLY = "failures_only"
    ALL = "all"



@dataclass
class AuditEntry:
    """
        Structured audit log entry for security events.

        Each entry captures the details of a security event including
        the event type, outcome, user identity, endpoint, policy, and
        request metadata. The to_json() method serializes the entry
        to a JSON string for machine processing.

        :param timestamp: When the event occurred.
        :param event_type: Category of event: "authentication", "authorization", or "violation".
        :param outcome: Result of the event: "success" or "failure".
        :param user_id: Identifier of the user involved, or None for unauthenticated.
        :param endpoint: The endpoint path that was accessed.
        :param policy: String representation of the policy that was evaluated.
        :param reason: Human-readable reason for the outcome.
        :param ip_address: IP address of the request origin.
        :param user_agent: User agent string from the request.
        :param request_id: Unique identifier for the request.
        :param correlation_id: Correlation identifier for tracing across services.
        :param extra: Additional metadata as a dictionary.
    """

    timestamp: datetime
    event_type: str
    outcome: str
    user_id: Optional[str]
    endpoint: Optional[str]
    policy: Optional[str]
    reason: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    correlation_id: Optional[str]
    extra: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        """
            Convert this entry to a dictionary representation.

            The timestamp is converted to an ISO 8601 string for
            serialization compatibility.

            :returns: A dictionary containing all entry fields.
        """
        rtnval = {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "outcome": self.outcome,
            "user_id": self.user_id,
            "endpoint": self.endpoint,
            "policy": self.policy,
            "reason": self.reason,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "extra": self.extra,
        }
        return rtnval

    def to_json(self) -> str:
        """
            Serialize this entry to a JSON string.

            :returns: A valid JSON string representation of this entry.
        """
        entry_dict = self.as_dict()
        rtnval = json.dumps(entry_dict)
        return rtnval



class AuditDestination:
    """
        Protocol for audit log destinations.

        Implementations of this protocol receive Audit_Entry objects
        and persist them to a storage backend such as a file, database,
        or external service. Both synchronous and asynchronous write
        methods are provided.
    """

    def write(self, entry: AuditEntry) -> None:
        """
            Write an audit entry to this destination.

            :param entry: The audit entry to write.
        """
        ...

    async def write_async(self, entry: AuditEntry) -> None:
        """
            Asynchronously write an audit entry to this destination.

            :param entry: The audit entry to write.
        """
        ...



class AuditLogger:
    """
        Logs security events for compliance and forensics.

        The Audit_Logger coordinates the recording of authentication attempts,
        authorization decisions, and policy violations. It supports configurable
        audit levels to control which events are recorded, multiple destinations
        for writing entries, and a query interface for retrieving historical
        entries.

        Entries are stored internally for query support and dispatched to all
        registered destinations.

        :param level: The audit level controlling which events are recorded.
        :param destinations: Optional list of AuditDestination instances.
    """

    def __init__(
        self,
        level: AuditLevel = AuditLevel.ALL,
        destinations: Optional[List[AuditDestination]] = None
    ):
        self._level = level
        self._destinations: List[AuditDestination] = destinations if destinations is not None else []
        self._entries: List[AuditEntry] = []
        return

    def _should_log(self, outcome: str) -> bool:
        """
            Determine whether an event with the given outcome should be logged
            based on the current audit level.

            :param outcome: The outcome of the event ("success" or "failure").

            :returns: True if the event should be logged.
        """
        if self._level == AuditLevel.NONE:
            return False

        if self._level == AuditLevel.FAILURES_ONLY:
            is_failure = outcome == "failure"
            return is_failure

        # AuditLevel.ALL
        return True

    def _dispatch(self, entry: AuditEntry) -> None:
        """
            Store the entry internally and write it to all registered
            destinations.

            :param entry: The audit entry to dispatch.
        """
        self._entries.append(entry)

        for destination in self._destinations:
            destination.write(entry)

        return

    def log_authentication(
        self,
        context: SecurityContext,
        provider: str,
        success: bool,
        endpoint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
            Log an authentication attempt.

            :param context: The security context resulting from authentication.
            :param provider: The name of the authentication provider used.
            :param success: Whether authentication succeeded.
            :param endpoint: The endpoint path being accessed.
            :param ip_address: IP address of the request origin.
            :param user_agent: User agent string from the request.
            :param request_id: Unique identifier for the request.
            :param correlation_id: Correlation identifier for tracing.
        """
        outcome = "success" if success is True else "failure"

        should_log = self._should_log(outcome)
        if should_log is not True:
            return

        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            event_type="authentication",
            outcome=outcome,
            user_id=context.user_id,
            endpoint=endpoint,
            policy=None,
            reason=None if success is True else "Authentication failed",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            correlation_id=correlation_id,
            extra={"provider": provider}
        )

        self._dispatch(entry)

        return

    def log_authorization(
        self,
        context: SecurityContext,
        policy: AccessPolicy,
        allowed: bool,
        reason: Optional[str] = None,
        endpoint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
            Log an authorization decision.

            :param context: The security context that was evaluated.
            :param policy: The access policy that was checked.
            :param allowed: Whether authorization was granted.
            :param reason: The reason for the decision.
            :param endpoint: The endpoint path being accessed.
            :param ip_address: IP address of the request origin.
            :param user_agent: User agent string from the request.
            :param request_id: Unique identifier for the request.
            :param correlation_id: Correlation identifier for tracing.
        """
        outcome = "success" if allowed is True else "failure"

        should_log = self._should_log(outcome)
        if should_log is not True:
            return

        policy_str = "roles={}, scopes={}, require_auth={}".format(
            policy.roles, policy.scopes, policy.require_auth
        )

        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            event_type="authorization",
            outcome=outcome,
            user_id=context.user_id,
            endpoint=endpoint,
            policy=policy_str,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            correlation_id=correlation_id,
        )

        self._dispatch(entry)

        return

    def log_violation(
        self,
        context: SecurityContext,
        policy: AccessPolicy,
        constraint: str,
        endpoint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
            Log a policy violation.

            Violations are always logged as failures. The constraint parameter
            describes the specific policy constraint that was not satisfied.

            :param context: The security context that violated the policy.
            :param policy: The access policy that was violated.
            :param constraint: Description of the specific constraint violated.
            :param endpoint: The endpoint path being accessed.
            :param ip_address: IP address of the request origin.
            :param user_agent: User agent string from the request.
            :param request_id: Unique identifier for the request.
            :param correlation_id: Correlation identifier for tracing.
        """
        outcome = "failure"

        should_log = self._should_log(outcome)
        if should_log is not True:
            return

        policy_str = "roles={}, scopes={}, require_auth={}".format(
            policy.roles, policy.scopes, policy.require_auth
        )

        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            event_type="violation",
            outcome=outcome,
            user_id=context.user_id,
            endpoint=endpoint,
            policy=policy_str,
            reason=constraint,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            correlation_id=correlation_id,
        )

        self._dispatch(entry)

        return

    def add_destination(self, destination: AuditDestination) -> None:
        """
            Add an audit log destination.

            :param destination: An AuditDestination instance to add.
        """
        self._destinations.append(destination)
        return

    def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        outcome: Optional[str] = None
    ) -> List[AuditEntry]:
        """
            Query historical audit entries with optional filters.

            All filter parameters are optional. When provided, only entries
            matching all specified filters are returned.

            :param start_time: Include entries at or after this time.
            :param end_time: Include entries at or before this time.
            :param event_type: Filter by event type.
            :param user_id: Filter by user identifier.
            :param outcome: Filter by outcome.

            :returns: A list of matching Audit_Entry objects.
        """
        results: List[AuditEntry] = []

        for entry in self._entries:
            if start_time is not None:
                if entry.timestamp < start_time:
                    continue

            if end_time is not None:
                if entry.timestamp > end_time:
                    continue

            if event_type is not None:
                if entry.event_type != event_type:
                    continue

            if user_id is not None:
                if entry.user_id != user_id:
                    continue

            if outcome is not None:
                if entry.outcome != outcome:
                    continue

            results.append(entry)

        return results
