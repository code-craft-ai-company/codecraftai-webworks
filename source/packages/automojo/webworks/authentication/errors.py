"""
.. module:: errors
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Error handling and security features for authentication.

.. moduleauthor:: Automation Mojo LLC

This module provides error handling classes and security features for the
authentication system including error sanitization, rate limiting, and
account lockout policies.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import logging
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple


# =============================================================================
# Authentication Error Classes
# =============================================================================

class AuthenticationError(Exception):
    """
        Base exception for authentication errors.
        
        This exception provides a safe way to represent authentication
        errors without leaking sensitive information. The error_code
        and safe_message are suitable for external responses, while
        internal_message can contain more detail for logging.
        
        :param error_code: A short error code identifier (e.g., "invalid_credentials").
        :param safe_message: A message safe to return to clients.
        :param internal_message: Detailed message for internal logging (not exposed).
        :param status_code: HTTP status code to return (default 401).
    """
    
    def __init__(
        self,
        error_code: str,
        safe_message: str,
        internal_message: Optional[str] = None,
        status_code: int = 401
    ):
        super().__init__(safe_message)
        self._error_code = error_code
        self._safe_message = safe_message
        self._internal_message = internal_message or safe_message
        self._status_code = status_code
    
    @property
    def error_code(self) -> str:
        """
            Get the error code identifier.
            
            :returns: The error code string.
        """
        return self._error_code
    
    @property
    def safe_message(self) -> str:
        """
            Get the message safe for external responses.
            
            :returns: The safe message string.
        """
        return self._safe_message
    
    @property
    def internal_message(self) -> str:
        """
            Get the detailed internal message for logging.
            
            :returns: The internal message string.
        """
        return self._internal_message
    
    @property
    def status_code(self) -> int:
        """
            Get the HTTP status code.
            
            :returns: The HTTP status code.
        """
        return self._status_code
    
    def to_response_dict(self) -> Dict[str, str]:
        """
            Convert to a dictionary safe for HTTP responses.
            
            :returns: Dictionary with error and error_description keys.
        """
        return {
            "error": self._error_code,
            "error_description": self._safe_message
        }


class InternalAuthenticationError(AuthenticationError):
    """
        Exception for internal authentication system errors.
        
        This exception represents errors that occur within the authentication
        system itself (e.g., database errors, configuration issues). It
        always returns a 500 status code and a generic safe message to
        avoid leaking internal details.
    """
    
    def __init__(
        self,
        internal_message: str,
        original_exception: Optional[Exception] = None
    ):
        safe_message = "An internal error occurred during authentication"
        super().__init__(
            error_code="internal_error",
            safe_message=safe_message,
            internal_message=internal_message,
            status_code=500
        )
        self._original_exception = original_exception
    
    @property
    def original_exception(self) -> Optional[Exception]:
        """
            Get the original exception that caused this error.
            
            :returns: The original exception, if any.
        """
        return self._original_exception


class RateLimitExceededError(AuthenticationError):
    """
        Exception raised when rate limit is exceeded.
    """
    
    def __init__(
        self,
        retry_after: Optional[int] = None,
        internal_message: Optional[str] = None
    ):
        safe_message = "Too many authentication attempts"
        if retry_after:
            safe_message += f". Please retry after {retry_after} seconds"
        
        super().__init__(
            error_code="rate_limit_exceeded",
            safe_message=safe_message,
            internal_message=internal_message,
            status_code=429
        )
        self._retry_after = retry_after
    
    @property
    def retry_after(self) -> Optional[int]:
        """
            Get the number of seconds to wait before retrying.
            
            :returns: Seconds to wait, or None if not specified.
        """
        return self._retry_after


class AccountLockedError(AuthenticationError):
    """
        Exception raised when an account is locked due to too many failures.
    """
    
    def __init__(
        self,
        locked_until: Optional[datetime] = None,
        internal_message: Optional[str] = None
    ):
        safe_message = "Account is temporarily locked due to too many failed attempts"
        
        super().__init__(
            error_code="account_locked",
            safe_message=safe_message,
            internal_message=internal_message,
            status_code=403
        )
        self._locked_until = locked_until
    
    @property
    def locked_until(self) -> Optional[datetime]:
        """
            Get the datetime when the account will be unlocked.
            
            :returns: Unlock datetime, or None if not specified.
        """
        return self._locked_until


# =============================================================================
# Credential Sanitization
# =============================================================================

# Patterns for detecting sensitive data
# These patterns require an assignment operator (=, :) or quotes to avoid false positives
# on natural language text like "The token is invalid"
_SENSITIVE_PATTERNS: List[Tuple[Pattern, str]] = [
    # Password patterns - require = or : followed by value
    (re.compile(r'password\s*[":=]\s*["\']?[^"\'\s,}]+["\']?', re.IGNORECASE), 'password=[REDACTED]'),
    (re.compile(r'passwd\s*[":=]\s*["\']?[^"\'\s,}]+["\']?', re.IGNORECASE), 'passwd=[REDACTED]'),
    (re.compile(r'pwd\s*[":=]\s*["\']?[^"\'\s,}]+["\']?', re.IGNORECASE), 'pwd=[REDACTED]'),
    
    # Token patterns - require = or : followed by value
    (re.compile(r'token\s*[":=]\s*["\']?[^"\'\s,}]+["\']?', re.IGNORECASE), 'token=[REDACTED]'),
    (re.compile(r'access_token\s*[":=]\s*["\']?[^"\'\s,}]+["\']?', re.IGNORECASE), 'access_token=[REDACTED]'),
    (re.compile(r'refresh_token\s*[":=]\s*["\']?[^"\'\s,}]+["\']?', re.IGNORECASE), 'refresh_token=[REDACTED]'),
    (re.compile(r'id_token\s*[":=]\s*["\']?[^"\'\s,}]+["\']?', re.IGNORECASE), 'id_token=[REDACTED]'),
    
    # API key patterns - require = or : followed by value
    (re.compile(r'api[_-]?key\s*[":=]\s*["\']?[^"\'\s,}]+["\']?', re.IGNORECASE), 'api_key=[REDACTED]'),
    (re.compile(r'apikey\s*[":=]\s*["\']?[^"\'\s,}]+["\']?', re.IGNORECASE), 'apikey=[REDACTED]'),
    
    # Secret patterns - require = or : followed by value
    (re.compile(r'secret\s*[":=]\s*["\']?[^"\'\s,}]+["\']?', re.IGNORECASE), 'secret=[REDACTED]'),
    (re.compile(r'client_secret\s*[":=]\s*["\']?[^"\'\s,}]+["\']?', re.IGNORECASE), 'client_secret=[REDACTED]'),
    
    # Authorization header (Base64 encoded credentials)
    (re.compile(r'Authorization\s*[":=]\s*["\']?Basic\s+[A-Za-z0-9+/=]+["\']?', re.IGNORECASE), 'Authorization=Basic [REDACTED]'),
    (re.compile(r'Authorization\s*[":=]\s*["\']?Bearer\s+[^\s"\']+["\']?', re.IGNORECASE), 'Authorization=Bearer [REDACTED]'),
    
    # Credential patterns - require = or : followed by value
    (re.compile(r'credential[s]?\s*[":=]\s*["\']?[^"\'\s,}]+["\']?', re.IGNORECASE), 'credentials=[REDACTED]'),
    
    # Session ID patterns - require = or : followed by value
    (re.compile(r'session[_-]?id\s*[":=]\s*["\']?[^"\'\s,}]+["\']?', re.IGNORECASE), 'session_id=[REDACTED]'),
    
    # Nonce patterns - require = or : followed by value
    (re.compile(r'nonce\s*[":=]\s*["\']?[^"\'\s,}]+["\']?', re.IGNORECASE), 'nonce=[REDACTED]'),
]


def sanitize_credentials(text: str) -> str:
    """
        Sanitize a string by removing or masking sensitive credential data.
        
        This function scans the input text for patterns that may contain
        sensitive authentication data (passwords, tokens, API keys, etc.)
        and replaces them with redacted placeholders.
        
        :param text: The text to sanitize.
        
        :returns: The sanitized text with credentials redacted.
    """
    if not text:
        return text
    
    result = text
    for pattern, replacement in _SENSITIVE_PATTERNS:
        result = pattern.sub(replacement, result)
    
    return result


def sanitize_dict(data: Dict[str, Any], sensitive_keys: Optional[Set[str]] = None) -> Dict[str, Any]:
    """
        Sanitize a dictionary by redacting values of sensitive keys.
        
        :param data: The dictionary to sanitize.
        :param sensitive_keys: Additional keys to treat as sensitive.
        
        :returns: A new dictionary with sensitive values redacted.
    """
    default_sensitive_keys = {
        'password', 'passwd', 'pwd', 'secret', 'token', 'access_token',
        'refresh_token', 'id_token', 'api_key', 'apikey', 'api-key',
        'client_secret', 'credentials', 'credential', 'session_id',
        'sessionid', 'nonce', 'authorization', 'auth'
    }
    
    all_sensitive_keys = default_sensitive_keys
    if sensitive_keys:
        all_sensitive_keys = all_sensitive_keys | sensitive_keys
    
    result = {}
    for key, value in data.items():
        key_lower = key.lower().replace('-', '_')
        if isinstance(value, dict):
            # Always recurse into nested dicts
            result[key] = sanitize_dict(value, sensitive_keys)
        elif key_lower in all_sensitive_keys:
            # Only redact non-dict values for sensitive keys
            result[key] = '[REDACTED]'
        elif isinstance(value, str):
            result[key] = sanitize_credentials(value)
        else:
            result[key] = value
    
    return result


def create_safe_error_response(
    error_code: str,
    error_description: str,
    include_details: bool = False,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
        Create a safe error response dictionary.
        
        This function creates an error response that is safe to return
        to clients, ensuring no sensitive information is leaked.
        
        :param error_code: The error code identifier.
        :param error_description: The error description.
        :param include_details: Whether to include additional details.
        :param details: Additional details to include (will be sanitized).
        
        :returns: A dictionary safe for HTTP responses.
    """
    response = {
        "error": error_code,
        "error_description": sanitize_credentials(error_description)
    }
    
    if include_details and details:
        response["details"] = sanitize_dict(details)
    
    return response


# =============================================================================
# Rate Limiting
# =============================================================================

@dataclass
class RateLimitConfig:
    """
        Configuration for rate limiting.
        
        :param max_attempts: Maximum number of attempts allowed in the window.
        :param window_seconds: Time window in seconds for counting attempts.
        :param lockout_seconds: Duration of lockout after exceeding limit.
    """
    max_attempts: int = 5
    window_seconds: int = 60
    lockout_seconds: int = 300


@dataclass
class RateLimitEntry:
    """
        Tracks rate limit state for a single key.
    """
    attempts: List[float] = field(default_factory=list)
    locked_until: Optional[float] = None


class RateLimiter:
    """
        Rate limiter for authentication attempts.
        
        This class tracks authentication attempts by key (e.g., IP address,
        username) and enforces configurable rate limits. When the limit
        is exceeded, subsequent attempts are blocked for a lockout period.
        
        Example usage::
        
            limiter = RateLimiter(RateLimitConfig(max_attempts=5, window_seconds=60))
            
            # Check if attempt is allowed
            if not limiter.is_allowed("192.168.1.1"):
                raise RateLimitExceededError()
            
            # Record a failed attempt
            limiter.record_attempt("192.168.1.1", success=False)
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
            Initialize the rate limiter.
            
            :param config: Rate limit configuration. Uses defaults if None.
        """
        self._config = config or RateLimitConfig()
        self._entries: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._lock = Lock()
    
    @property
    def config(self) -> RateLimitConfig:
        """
            Get the rate limit configuration.
            
            :returns: The RateLimitConfig instance.
        """
        return self._config
    
    def is_allowed(self, key: str) -> bool:
        """
            Check if an authentication attempt is allowed for the given key.
            
            :param key: The rate limit key (e.g., IP address, username).
            
            :returns: True if the attempt is allowed, False otherwise.
        """
        with self._lock:
            entry = self._entries[key]
            now = time.time()
            
            # Check if currently locked out
            if entry.locked_until is not None:
                if now < entry.locked_until:
                    return False
                else:
                    # Lockout expired, reset
                    entry.locked_until = None
                    entry.attempts = []
            
            # Clean up old attempts outside the window
            window_start = now - self._config.window_seconds
            entry.attempts = [t for t in entry.attempts if t > window_start]
            
            # Check if under the limit
            return len(entry.attempts) < self._config.max_attempts
    
    def record_attempt(self, key: str, success: bool = False) -> None:
        """
            Record an authentication attempt.
            
            :param key: The rate limit key.
            :param success: Whether the attempt was successful.
        """
        with self._lock:
            entry = self._entries[key]
            now = time.time()
            
            if success:
                # Successful attempt resets the counter
                entry.attempts = []
                entry.locked_until = None
            else:
                # Record failed attempt
                entry.attempts.append(now)
                
                # Clean up old attempts
                window_start = now - self._config.window_seconds
                entry.attempts = [t for t in entry.attempts if t > window_start]
                
                # Check if limit exceeded
                if len(entry.attempts) >= self._config.max_attempts:
                    entry.locked_until = now + self._config.lockout_seconds
    
    def get_remaining_attempts(self, key: str) -> int:
        """
            Get the number of remaining attempts for a key.
            
            :param key: The rate limit key.
            
            :returns: Number of remaining attempts, or 0 if locked out.
        """
        with self._lock:
            entry = self._entries[key]
            now = time.time()
            
            # Check if locked out
            if entry.locked_until is not None and now < entry.locked_until:
                return 0
            
            # Clean up old attempts
            window_start = now - self._config.window_seconds
            current_attempts = len([t for t in entry.attempts if t > window_start])
            
            return max(0, self._config.max_attempts - current_attempts)
    
    def get_retry_after(self, key: str) -> Optional[int]:
        """
            Get the number of seconds until the key can retry.
            
            :param key: The rate limit key.
            
            :returns: Seconds until retry is allowed, or None if not locked.
        """
        with self._lock:
            entry = self._entries[key]
            now = time.time()
            
            if entry.locked_until is not None and now < entry.locked_until:
                return int(entry.locked_until - now) + 1
            
            return None
    
    def reset(self, key: str) -> None:
        """
            Reset the rate limit state for a key.
            
            :param key: The rate limit key to reset.
        """
        with self._lock:
            if key in self._entries:
                del self._entries[key]
    
    def clear_all(self) -> None:
        """
            Clear all rate limit state.
        """
        with self._lock:
            self._entries.clear()


# =============================================================================
# Account Lockout Policy
# =============================================================================

@dataclass
class LockoutConfig:
    """
        Configuration for account lockout policy.
        
        :param max_failures: Maximum failures before lockout.
        :param lockout_duration_seconds: Duration of lockout in seconds.
        :param reset_after_seconds: Reset failure count after this many seconds of no failures.
    """
    max_failures: int = 5
    lockout_duration_seconds: int = 900  # 15 minutes
    reset_after_seconds: int = 3600  # 1 hour


@dataclass
class AccountLockoutEntry:
    """
        Tracks lockout state for a single account.
    """
    failure_count: int = 0
    last_failure: Optional[float] = None
    locked_until: Optional[float] = None


class AccountLockoutPolicy:
    """
        Account lockout policy for preventing brute force attacks.
        
        This class tracks failed authentication attempts per account
        and locks accounts after too many failures. Unlike rate limiting
        which is typically per-IP, this is per-account.
        
        Example usage::
        
            policy = AccountLockoutPolicy(LockoutConfig(max_failures=5))
            
            # Check if account is locked
            if policy.is_locked("user@example.com"):
                raise AccountLockedError()
            
            # Record a failed attempt
            policy.record_failure("user@example.com")
    """
    
    def __init__(self, config: Optional[LockoutConfig] = None):
        """
            Initialize the lockout policy.
            
            :param config: Lockout configuration. Uses defaults if None.
        """
        self._config = config or LockoutConfig()
        self._entries: Dict[str, AccountLockoutEntry] = defaultdict(AccountLockoutEntry)
        self._lock = Lock()
    
    @property
    def config(self) -> LockoutConfig:
        """
            Get the lockout configuration.
            
            :returns: The LockoutConfig instance.
        """
        return self._config
    
    def is_locked(self, account_id: str) -> bool:
        """
            Check if an account is currently locked.
            
            :param account_id: The account identifier.
            
            :returns: True if the account is locked, False otherwise.
        """
        with self._lock:
            entry = self._entries.get(account_id)
            if entry is None:
                return False
            
            now = time.time()
            
            # Check if lockout has expired
            if entry.locked_until is not None:
                if now < entry.locked_until:
                    return True
                else:
                    # Lockout expired, reset
                    entry.locked_until = None
                    entry.failure_count = 0
                    return False
            
            return False
    
    def record_failure(self, account_id: str) -> bool:
        """
            Record a failed authentication attempt.
            
            :param account_id: The account identifier.
            
            :returns: True if the account is now locked, False otherwise.
        """
        with self._lock:
            entry = self._entries[account_id]
            now = time.time()
            
            # Check if we should reset the failure count
            if entry.last_failure is not None:
                time_since_last = now - entry.last_failure
                if time_since_last > self._config.reset_after_seconds:
                    entry.failure_count = 0
            
            entry.failure_count += 1
            entry.last_failure = now
            
            # Check if we should lock the account
            if entry.failure_count >= self._config.max_failures:
                entry.locked_until = now + self._config.lockout_duration_seconds
                return True
            
            return False
    
    def record_success(self, account_id: str) -> None:
        """
            Record a successful authentication, resetting the failure count.
            
            :param account_id: The account identifier.
        """
        with self._lock:
            if account_id in self._entries:
                entry = self._entries[account_id]
                entry.failure_count = 0
                entry.last_failure = None
                entry.locked_until = None
    
    def get_failure_count(self, account_id: str) -> int:
        """
            Get the current failure count for an account.
            
            :param account_id: The account identifier.
            
            :returns: The number of recent failures.
        """
        with self._lock:
            entry = self._entries.get(account_id)
            if entry is None:
                return 0
            return entry.failure_count
    
    def get_locked_until(self, account_id: str) -> Optional[datetime]:
        """
            Get the datetime when the account will be unlocked.
            
            :param account_id: The account identifier.
            
            :returns: Unlock datetime, or None if not locked.
        """
        with self._lock:
            entry = self._entries.get(account_id)
            if entry is None or entry.locked_until is None:
                return None
            
            now = time.time()
            if now >= entry.locked_until:
                return None
            
            return datetime.utcnow() + timedelta(seconds=entry.locked_until - now)
    
    def unlock(self, account_id: str) -> None:
        """
            Manually unlock an account.
            
            :param account_id: The account identifier.
        """
        with self._lock:
            if account_id in self._entries:
                entry = self._entries[account_id]
                entry.locked_until = None
                entry.failure_count = 0
    
    def clear_all(self) -> None:
        """
            Clear all lockout state.
        """
        with self._lock:
            self._entries.clear()


# =============================================================================
# Safe Error Response Handling
# =============================================================================

def handle_authentication_error(
    error: Exception,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
        Handle an authentication error and return a safe response.
        
        This function takes any exception that occurred during authentication
        and returns a safe error response dictionary. For AuthenticationError
        subclasses, it uses the safe message. For other exceptions, it returns
        a generic internal error response.
        
        :param error: The exception that occurred.
        :param logger: Optional logger for logging the error.
        
        :returns: A dictionary safe for HTTP responses.
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    if isinstance(error, AuthenticationError):
        # Log the internal message
        logger.warning(
            f"Authentication error: {error.error_code} - {error.internal_message}"
        )
        return error.to_response_dict()
    else:
        # Unknown error - log full details but return generic response
        logger.error(
            f"Internal authentication error: {type(error).__name__} - {str(error)}",
            exc_info=True
        )
        return {
            "error": "internal_error",
            "error_description": "An internal error occurred during authentication"
        }


def wrap_internal_error(error: Exception) -> InternalAuthenticationError:
    """
        Wrap an unexpected exception in an InternalAuthenticationError.
        
        :param error: The original exception.
        
        :returns: An InternalAuthenticationError wrapping the original.
    """
    return InternalAuthenticationError(
        internal_message=f"{type(error).__name__}: {str(error)}",
        original_exception=error
    )

