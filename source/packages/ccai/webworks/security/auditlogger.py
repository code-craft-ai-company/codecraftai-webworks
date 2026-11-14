"""
.. module:: auditlogger
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Audit logging for security events including authentication attempts,
        authorization decisions, and policy violations.

.. moduleauthor:: Code Craft AI LLC

This module provides the audit logging infrastructure for the security framework.
It includes the AuditLevel enum for configuring logging verbosity, the AuditEntry
dataclass for structured log entries, the AuditDestination protocol for pluggable
log destinations, and the AuditLogger class that coordinates logging of security
events.

The AuditLogger supports multiple destinations, configurable audit levels, and
provides a query interface for retrieving historical security events. Logging is
designed to avoid blocking request processing.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import collections
import json
import logging
import queue
import threading

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Deque, Dict, List, Optional

from ccai.webworks.security.accesspolicy import AccessPolicy
from ccai.webworks.security.securitycontext import SecurityContext


# Module-level logger. A destination that fails must not fail the request
# being audited, so its error is reported here instead of being raised.
logger = logging.getLogger(__name__)


#: Number of entries the logger keeps in memory for :meth:`AuditLogger.query`
#: when no other limit is given. Older entries are dropped from memory; they
#: remain in the destinations they were written to.
DEFAULT_MAX_ENTRIES: int = 10000


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

    async def write_async(self, entry: AuditEntry) -> None:
        """
            Asynchronously write an audit entry to this destination.

            :param entry: The audit entry to write.
        """



class FileAuditDestination:
    """
        Audit destination that appends each entry to a file as one line of
        JSON.

        :param file_path: Path of the audit log file. It is created when
            the first entry is written; its directory must exist.
    """

    def __init__(self, file_path: str):
        self._file_path = file_path
        self._lock = threading.Lock()
        return

    @property
    def file_path(self) -> str:
        """
            Get the path of the audit log file.

            :returns: The file path.
        """
        rtnval = self._file_path
        return rtnval

    def write(self, entry: AuditEntry) -> None:
        """
            Append an audit entry to the file.

            :param entry: The audit entry to write.
        """
        line = entry.to_json()

        with self._lock:
            with open(self._file_path, "a", encoding="utf-8") as log_file:
                log_file.write(line)
                log_file.write("\n")

        return

    async def write_async(self, entry: AuditEntry) -> None:
        """
            Asynchronously append an audit entry to the file.

            :param entry: The audit entry to write.
        """
        self.write(entry)
        return


class AuditLogger:
    """
        Logs security events for compliance and forensics.

        The Audit_Logger coordinates the recording of authentication attempts,
        authorization decisions, and policy violations. It supports configurable
        audit levels to control which events are recorded, multiple destinations
        for writing entries, and a query interface for retrieving historical
        entries.

        Entries are stored internally for query support and dispatched to all
        registered destinations. The internal store is bounded: it keeps
        the most recent ``max_entries`` entries and, when ``retention`` is
        set, drops entries older than that. A long-running process
        therefore does not grow with every request; the destinations are
        the durable record.

        A destination that raises does not fail the request being audited:
        the error is logged and the remaining destinations are still
        written. With ``background=True`` destinations are written by a
        worker thread, so a slow sink does not delay the request either;
        call :meth:`flush` to wait for pending entries and :meth:`close`
        when the logger is no longer needed.

        :param level: The audit level controlling which events are recorded.
        :param destinations: Optional list of AuditDestination instances.
        :param max_entries: Largest number of entries kept in memory for
            :meth:`query`. ``None`` removes the limit.
        :param retention: How long an entry is kept in memory. ``None``
            keeps entries until ``max_entries`` displaces them.
        :param background: If True, destinations are written by a
            background worker thread instead of the calling thread.
    """

    def __init__(
        self,
        level: AuditLevel = AuditLevel.ALL,
        destinations: Optional[List[AuditDestination]] = None,
        max_entries: Optional[int] = DEFAULT_MAX_ENTRIES,
        retention: Optional[timedelta] = None,
        background: bool = False
    ):
        self._level = level
        self._destinations: List[AuditDestination] = destinations if destinations is not None else []
        self._max_entries = max_entries
        self._retention = retention
        self._entries: Deque[AuditEntry] = collections.deque(maxlen=max_entries)
        self._entries_lock = threading.Lock()

        self._background = background
        self._pending: Optional["queue.Queue[Optional[AuditEntry]]"] = None
        self._worker: Optional[threading.Thread] = None

        if background is True:
            self._pending = queue.Queue()
            self._worker = threading.Thread(
                target=self._write_pending_entries,
                name="webworks-audit-logger",
                daemon=True
            )
            self._worker.start()

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
        with self._entries_lock:
            self._prune_expired_entries(entry.timestamp)
            self._entries.append(entry)

        if self._pending is not None:
            self._pending.put(entry)
        else:
            self._write_to_destinations(entry)

        return

    def _prune_expired_entries(self, now: datetime) -> None:
        """
            Drop the entries that are older than the retention period.

            Entries are stored in the order they were logged, so the
            expired ones are at the front.

            :param now: The current time.
        """
        if self._retention is not None:
            oldest_kept = now - self._retention

            while len(self._entries) > 0 and self._entries[0].timestamp < oldest_kept:
                self._entries.popleft()

        return

    def _write_to_destinations(self, entry: AuditEntry) -> None:
        """
            Write an entry to every registered destination.

            A destination that raises is reported and skipped; the others
            are still written and the caller is not interrupted.

            :param entry: The audit entry to write.
        """
        for destination in list(self._destinations):
            try:
                destination.write(entry)
            except Exception:
                logger.exception(
                    "Audit destination %r failed to write a %s entry",
                    destination, entry.event_type
                )

        return

    def _write_pending_entries(self) -> None:
        """
            Body of the background worker: write queued entries to the
            destinations until the logger is closed.
        """
        pending = self._pending

        while True:
            entry = pending.get()

            try:
                if entry is None:
                    break
                self._write_to_destinations(entry)
            finally:
                pending.task_done()

        return

    def flush(self) -> None:
        """
            Wait until every entry logged so far has been written to the
            destinations. Returns at once when the logger writes on the
            calling thread.
        """
        if self._pending is not None:
            self._pending.join()

        return

    def close(self) -> None:
        """
            Write the pending entries and stop the background worker.
            Entries logged afterwards are written on the calling thread.
        """
        if self._pending is not None:
            pending = self._pending
            worker = self._worker

            self._pending = None
            self._worker = None

            pending.put(None)
            if worker is not None:
                worker.join()

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

        with self._entries_lock:
            self._prune_expired_entries(datetime.now(timezone.utc))
            stored_entries = list(self._entries)

        for entry in stored_entries:
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
