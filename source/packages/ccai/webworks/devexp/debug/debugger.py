"""
    Interactive debugger for the webworks framework.

    This module provides the :class:`InteractiveDebugger` class that
    enables browser-based interactive debugging when errors occur in
    debug mode. The debugger supports PIN-based security, expression
    evaluation in the context of each stack frame, stack frame
    navigation, and session timeout.

    The interactive debugger is disabled by default and requires
    explicit opt-in via the ``interactive`` parameter.

    Evaluating an expression in a stack frame is arbitrary code execution
    with the privileges of the server process. There is no sandbox, and
    none is pretended: the PIN is the only thing between a caller and the
    process. The PIN is therefore generated randomly when none is given,
    compared in constant time, and locked after repeated failures.
"""

import hmac
import secrets
import time
import uuid

from typing import Any, Dict, List, Optional

from ccai.webworks.devexp.debug.errorhandler import FrameInfo


# =============================================================================
# Constants
# =============================================================================

DEFAULT_TIMEOUT = 300
"""Default session timeout in seconds (5 minutes)."""

DEFAULT_MAX_PIN_ATTEMPTS = 5
"""Number of consecutive wrong PINs after which the debugger locks."""

GENERATED_PIN_DIGITS = 9
"""Number of digits in a generated PIN."""

INVALID_PIN_MESSAGE = "Invalid PIN"
"""Error message returned when an incorrect PIN is provided."""

LOCKED_OUT_MESSAGE = "Too many failed PIN attempts; the debugger is locked until the server restarts"
"""Error message returned once the debugger has locked after repeated wrong PINs."""

DEBUGGER_DISABLED_MESSAGE = "Interactive debugger is not enabled"
"""Error message returned when the debugger is used while disabled."""

SESSION_NOT_FOUND_MESSAGE = "Session not found or expired"
"""Error message returned when a session ID is invalid or expired."""

FRAME_INDEX_OUT_OF_RANGE_MESSAGE = "Frame index out of range"
"""Error message returned when a frame index is invalid."""


# =============================================================================
# PIN Generation
# =============================================================================

def generate_pin() -> str:
    """
        Generate a random debugger PIN.

        The PIN comes from the operating system's secure random source and
        is formatted in groups of three digits (``123-456-789``) so it can
        be read from a console and typed into a browser.

        :returns: The PIN string.
    """
    digits = "".join(str(secrets.randbelow(10)) for _ in range(GENERATED_PIN_DIGITS))

    groups = []
    for start in range(0, len(digits), 3):
        groups.append(digits[start:start + 3])

    pin = "-".join(groups)

    return pin


# =============================================================================
# DebugSession
# =============================================================================

class DebugSession:
    """
        Represents an active debug session for a single exception.

        Stores the exception, stack frames, and the timestamp of the
        last activity for timeout management.

        :param session_id: The unique session identifier.
        :param exception: The exception being debugged.
        :param frames: The list of stack frame info objects.
        :param frame_locals: The list of actual frame local dictionaries
            for expression evaluation.
        :param frame_globals: The list of actual frame global dictionaries
            for expression evaluation.
    """

    def __init__(
        self,
        session_id: str,
        exception: Exception,
        frames: List[FrameInfo],
        frame_locals: Optional[List[Dict[str, Any]]] = None,
        frame_globals: Optional[List[Dict[str, Any]]] = None,
    ):
        """
            Construct a DebugSession.

            :param session_id: The unique session identifier.
            :param exception: The exception being debugged.
            :param frames: The list of FrameInfo objects.
            :param frame_locals: The list of actual frame local dicts.
            :param frame_globals: The list of actual frame global dicts.
        """
        self._session_id = session_id
        self._exception = exception
        self._frames = list(frames)
        self._frame_locals = list(frame_locals) if frame_locals is not None else []
        self._frame_globals = list(frame_globals) if frame_globals is not None else []
        self._last_activity = time.time()
        return

    @property
    def session_id(self) -> str:
        """
            The unique session identifier.

            :returns: The session ID string.
        """
        return self._session_id

    @property
    def exception(self) -> Exception:
        """
            The exception being debugged.

            :returns: The exception instance.
        """
        return self._exception

    @property
    def frames(self) -> List[FrameInfo]:
        """
            The stack frames for this session.

            :returns: A list of FrameInfo objects.
        """
        return list(self._frames)

    @property
    def frame_locals(self) -> List[Dict[str, Any]]:
        """
            The actual local variable dictionaries for each frame.

            :returns: A list of dictionaries.
        """
        return list(self._frame_locals)

    @property
    def frame_globals(self) -> List[Dict[str, Any]]:
        """
            The actual global variable dictionaries for each frame.

            :returns: A list of dictionaries.
        """
        return list(self._frame_globals)

    @property
    def last_activity(self) -> float:
        """
            The timestamp of the last activity.

            :returns: A float timestamp.
        """
        return self._last_activity

    def touch(self) -> None:
        """
            Update the last activity timestamp to the current time.
        """
        self._last_activity = time.time()
        return

    @property
    def frame_count(self) -> int:
        """
            The number of stack frames in this session.

            :returns: The frame count integer.
        """
        count = len(self._frames)
        return count


# =============================================================================
# InteractiveDebugger
# =============================================================================

class InteractiveDebugger:
    """
        Browser-based interactive debugger for error pages.

        Supports PIN-based security to prevent unauthorized access,
        expression evaluation in the context of each stack frame,
        stack frame navigation, and automatic session timeout.

        The debugger is disabled by default and must be explicitly
        enabled.

        :param pin: The security PIN required for access. A random PIN is
            generated when ``None``; read it from :attr:`pin` and show it
            on the server console.
        :param timeout: Session timeout in seconds.
        :param enabled: Whether the debugger is enabled.
        :param max_attempts: Consecutive wrong PINs after which the
            debugger locks.
    """

    def __init__(
        self,
        pin: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        enabled: bool = False,
        max_attempts: int = DEFAULT_MAX_PIN_ATTEMPTS,
    ):
        """
            Construct an InteractiveDebugger.

            :param pin: The security PIN for authorization. A random PIN
                is generated when ``None``.
            :param timeout: Session timeout in seconds.
            :param enabled: Whether the debugger is enabled.
            :param max_attempts: Consecutive wrong PINs after which the
                debugger locks until the process restarts.

            :raises ValueError: If a PIN is given that is not a non-empty
                string. A debugger must never be reachable without a PIN.
        """
        if pin is None:
            pin = generate_pin()
        elif not isinstance(pin, str) or len(pin) == 0:
            errmsg = "The debugger PIN must be a non-empty string."
            raise ValueError(errmsg)

        self._pin = pin
        self._timeout = timeout
        self._enabled = enabled
        self._max_attempts = max_attempts
        self._failed_attempts = 0
        self._sessions: Dict[str, DebugSession] = {}
        return

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def pin(self) -> str:
        """
            The security PIN for the debugger.

            :returns: The PIN string.
        """
        return self._pin

    @property
    def timeout(self) -> int:
        """
            The session timeout in seconds.

            :returns: The timeout integer.
        """
        return self._timeout

    @property
    def enabled(self) -> bool:
        """
            Whether the debugger is enabled.

            :returns: True if the debugger is active.
        """
        return self._enabled

    @property
    def locked(self) -> bool:
        """
            Whether the debugger has locked after repeated wrong PINs.

            :returns: True if no further PIN attempts are accepted.
        """
        is_locked = self._failed_attempts >= self._max_attempts
        return is_locked

    @property
    def session_count(self) -> int:
        """
            The number of active debug sessions.

            :returns: The session count integer.
        """
        count = len(self._sessions)
        return count

    # -------------------------------------------------------------------------
    # Session Management
    # -------------------------------------------------------------------------

    def check_pin(self, pin: Any) -> Optional[str]:
        """
            Check a PIN presented by a caller.

            The comparison takes the same time whether or not the PIN is
            right. Each wrong PIN counts toward the lockout; a right PIN
            resets the count. Once locked, every attempt is refused, the
            right PIN included, until the process restarts.

            :param pin: The PIN presented by the caller.

            :returns: ``None`` if the PIN is accepted, otherwise the error
                message to return to the caller.
        """
        if self._enabled is not True:
            return DEBUGGER_DISABLED_MESSAGE

        if self.locked:
            return LOCKED_OUT_MESSAGE

        matches = False
        if isinstance(pin, str):
            matches = hmac.compare_digest(pin.encode("utf-8"), self._pin.encode("utf-8"))

        if not matches:
            self._failed_attempts += 1
            return INVALID_PIN_MESSAGE

        self._failed_attempts = 0

        return None

    def create_session(
        self,
        exception: Exception,
        frames: List[FrameInfo],
        frame_locals: Optional[List[Dict[str, Any]]] = None,
        frame_globals: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
            Create a debug session for an exception.

            Cleans up expired sessions before creating a new one.

            :param exception: The exception to debug.
            :param frames: The list of FrameInfo objects.
            :param frame_locals: Optional list of actual frame local dicts.
            :param frame_globals: Optional list of actual frame global dicts.

            :returns: The session ID string.

            :raises RuntimeError: If the debugger is not enabled.
        """
        if self._enabled is not True:
            errmsg = DEBUGGER_DISABLED_MESSAGE
            raise RuntimeError(errmsg)

        self._cleanup_expired()

        session_id = str(uuid.uuid4())
        session = DebugSession(
            session_id=session_id,
            exception=exception,
            frames=frames,
            frame_locals=frame_locals,
            frame_globals=frame_globals,
        )
        self._sessions[session_id] = session

        return session_id

    def get_session(self, session_id: str) -> Optional[DebugSession]:
        """
            Get a debug session by ID.

            :param session_id: The session ID to look up.

            :returns: The DebugSession or None if not found or expired.
        """
        self._cleanup_expired()

        session = self._sessions.get(session_id)

        return session

    def get_frames(self, session_id: str, pin: str) -> Dict[str, Any]:
        """
            Get the stack frames for a debug session.

            :param session_id: The debug session ID.
            :param pin: The security PIN for authorization.

            :returns: A dictionary with ``frames`` key containing frame
                info or ``error`` key with an error message.
        """
        pin_error = self.check_pin(pin)
        if pin_error is not None:
            result = {"error": pin_error}
            return result

        self._cleanup_expired()

        session = self._sessions.get(session_id)
        if session is None:
            result = {"error": SESSION_NOT_FOUND_MESSAGE}
            return result

        session.touch()

        frame_list = []
        for idx, frame in enumerate(session.frames):
            frame_data = {
                "index": idx,
                "filename": frame.filename,
                "lineno": frame.lineno,
                "function": frame.function,
            }
            frame_list.append(frame_data)

        result = {"frames": frame_list}

        return result

    # -------------------------------------------------------------------------
    # Expression Evaluation
    # -------------------------------------------------------------------------

    def evaluate(
        self,
        session_id: str,
        frame_index: int,
        expression: str,
        pin: str,
    ) -> Dict[str, Any]:
        """
            Evaluate a Python expression in the context of a stack frame.

            The expression is evaluated with the frame's own globals and
            locals, so it sees what the code at that frame saw: built-in
            functions, imported modules and module-level names as well as
            local variables. This is unrestricted code execution; the PIN
            check is the access control.

            :param session_id: The debug session ID.
            :param frame_index: The index of the stack frame.
            :param expression: The Python expression to evaluate.
            :param pin: The security PIN for authorization.

            :returns: A dictionary with ``result`` key containing the
                string representation of the evaluation result, or
                ``error`` key with an error message.
        """
        pin_error = self.check_pin(pin)
        if pin_error is not None:
            result = {"error": pin_error}
            return result

        self._cleanup_expired()

        session = self._sessions.get(session_id)
        if session is None:
            result = {"error": SESSION_NOT_FOUND_MESSAGE}
            return result

        session.touch()

        if frame_index < 0 or frame_index >= session.frame_count:
            result = {"error": FRAME_INDEX_OUT_OF_RANGE_MESSAGE}
            return result

        # Get the local and global variables for the frame
        if frame_index < len(session.frame_locals):
            local_vars = session.frame_locals[frame_index]
        else:
            local_vars = {}

        if frame_index < len(session.frame_globals):
            global_vars = session.frame_globals[frame_index]
        else:
            # Without the frame's globals, eval supplies the built-ins.
            global_vars = {}

        try:
            eval_result = eval(expression, global_vars, local_vars)  # noqa: S307
            result = {"result": repr(eval_result)}
        except Exception as exc:
            result = {"error": "{}: {}".format(type(exc).__name__, str(exc))}

        return result

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def _cleanup_expired(self) -> None:
        """
            Remove expired debug sessions.

            A session is expired if the time since its last activity
            exceeds the configured timeout.
        """
        current_time = time.time()
        expired_ids = []

        for session_id, session in self._sessions.items():
            elapsed = current_time - session.last_activity
            if elapsed > self._timeout:
                expired_ids.append(session_id)

        for session_id in expired_ids:
            del self._sessions[session_id]

        return
