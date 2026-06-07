"""
    Interactive debugger for the webworks framework.

    This module provides the :class:`InteractiveDebugger` class that
    enables browser-based interactive debugging when errors occur in
    debug mode. The debugger supports PIN-based security, expression
    evaluation in the context of each stack frame, stack frame
    navigation, and session timeout.

    The interactive debugger is disabled by default and requires
    explicit opt-in via the ``interactive`` parameter.
"""

import time
import uuid

from typing import Any, Dict, List, Optional

from ccai.webworks.devexp.debug.errorhandler import FrameInfo


# =============================================================================
# Constants
# =============================================================================

DEFAULT_TIMEOUT = 300
"""Default session timeout in seconds (5 minutes)."""

INVALID_PIN_MESSAGE = "Invalid PIN"
"""Error message returned when an incorrect PIN is provided."""

SESSION_NOT_FOUND_MESSAGE = "Session not found or expired"
"""Error message returned when a session ID is invalid or expired."""

FRAME_INDEX_OUT_OF_RANGE_MESSAGE = "Frame index out of range"
"""Error message returned when a frame index is invalid."""


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
    """

    def __init__(
        self,
        session_id: str,
        exception: Exception,
        frames: List[FrameInfo],
        frame_locals: Optional[List[Dict[str, Any]]] = None,
    ):
        """
            Construct a DebugSession.

            :param session_id: The unique session identifier.
            :param exception: The exception being debugged.
            :param frames: The list of FrameInfo objects.
            :param frame_locals: The list of actual frame local dicts.
        """
        self._session_id = session_id
        self._exception = exception
        self._frames = list(frames)
        self._frame_locals = list(frame_locals) if frame_locals is not None else []
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

        :param pin: The security PIN required for access.
        :param timeout: Session timeout in seconds.
        :param enabled: Whether the debugger is enabled.
    """

    def __init__(
        self,
        pin: str,
        timeout: int = DEFAULT_TIMEOUT,
        enabled: bool = False,
    ):
        """
            Construct an InteractiveDebugger.

            :param pin: The security PIN for authorization.
            :param timeout: Session timeout in seconds.
            :param enabled: Whether the debugger is enabled.
        """
        self._pin = pin
        self._timeout = timeout
        self._enabled = enabled
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

    def create_session(
        self,
        exception: Exception,
        frames: List[FrameInfo],
        frame_locals: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
            Create a debug session for an exception.

            Cleans up expired sessions before creating a new one.

            :param exception: The exception to debug.
            :param frames: The list of FrameInfo objects.
            :param frame_locals: Optional list of actual frame local dicts.

            :returns: The session ID string.

            :raises RuntimeError: If the debugger is not enabled.
        """
        if self._enabled is not True:
            errmsg = "Interactive debugger is not enabled"
            raise RuntimeError(errmsg)

        self._cleanup_expired()

        session_id = str(uuid.uuid4())
        session = DebugSession(
            session_id=session_id,
            exception=exception,
            frames=frames,
            frame_locals=frame_locals,
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
        if pin != self._pin:
            result = {"error": INVALID_PIN_MESSAGE}
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

            :param session_id: The debug session ID.
            :param frame_index: The index of the stack frame.
            :param expression: The Python expression to evaluate.
            :param pin: The security PIN for authorization.

            :returns: A dictionary with ``result`` key containing the
                string representation of the evaluation result, or
                ``error`` key with an error message.
        """
        if pin != self._pin:
            result = {"error": INVALID_PIN_MESSAGE}
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

        # Get the local variables for the frame
        if frame_index < len(session.frame_locals):
            local_vars = session.frame_locals[frame_index]
        else:
            local_vars = {}

        try:
            eval_result = eval(expression, {"__builtins__": {}}, local_vars)
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
