"""
    Tests for the :class:`InteractiveDebugger` and :class:`DebugSession`
    classes.

    This module tests PIN-based security, expression evaluation in
    frame context, stack frame navigation, session timeout, and
    opt-in activation.
"""

import time

from automojo.webworks.devexp.debug.debugger import (
    DebugSession,
    InteractiveDebugger,
    INVALID_PIN_MESSAGE,
    SESSION_NOT_FOUND_MESSAGE,
    FRAME_INDEX_OUT_OF_RANGE_MESSAGE,
)
from automojo.webworks.devexp.debug.errorhandler import FrameInfo


# =============================================================================
# Helpers
# =============================================================================

def _make_frames(count: int = 3) -> list:
    """
        Create a list of FrameInfo objects for testing.

        :param count: The number of frames to create.

        :returns: A list of FrameInfo objects.
    """
    frames = []

    for idx in range(count):
        frame = FrameInfo(
            filename="/test/file_{}.py".format(idx),
            lineno=(idx + 1) * 10,
            function="func_{}".format(idx),
            code_context=["line {}\n".format(idx)],
            highlight_line=0,
            locals={"var_{}".format(idx): str(idx)},
        )
        frames.append(frame)

    return frames


def _make_frame_locals(count: int = 3) -> list:
    """
        Create a list of local variable dictionaries for testing.

        :param count: The number of frame local dicts to create.

        :returns: A list of dictionaries.
    """
    frame_locals = []

    for idx in range(count):
        local_dict = {
            "x": idx * 10,
            "name": "frame_{}".format(idx),
            "items": list(range(idx + 1)),
        }
        frame_locals.append(local_dict)

    return frame_locals


def _make_exception(message: str = "test error") -> Exception:
    """
        Create an exception for testing.

        :param message: The exception message.

        :returns: An exception instance.
    """
    try:
        raise ValueError(message)
    except ValueError as exc:
        return exc


# =============================================================================
# DebugSession Tests
# =============================================================================

def test_debug_session_construction():
    """
        Test that DebugSession stores all provided attributes.
    """
    frames = _make_frames(count=2)
    frame_locals = _make_frame_locals(count=2)
    exception = _make_exception("session test")

    session = DebugSession(
        session_id="test-session-1",
        exception=exception,
        frames=frames,
        frame_locals=frame_locals,
    )

    if session.session_id != "test-session-1":
        errmsg = "Expected session_id 'test-session-1', got '{}'".format(
            session.session_id,
        )
        raise AssertionError(errmsg)

    if session.frame_count != 2:
        errmsg = "Expected frame_count 2, got {}".format(session.frame_count)
        raise AssertionError(errmsg)

    if len(session.frame_locals) != 2:
        errmsg = "Expected 2 frame_locals, got {}".format(len(session.frame_locals))
        raise AssertionError(errmsg)

    return


def test_debug_session_touch_updates_timestamp():
    """
        Test that touch() updates the last_activity timestamp.
    """
    frames = _make_frames(count=1)
    exception = _make_exception()

    session = DebugSession(
        session_id="touch-test",
        exception=exception,
        frames=frames,
    )

    initial_time = session.last_activity
    time.sleep(0.05)
    session.touch()
    updated_time = session.last_activity

    if updated_time <= initial_time:
        errmsg = "Expected updated timestamp > initial, got {} <= {}".format(
            updated_time, initial_time,
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# InteractiveDebugger Construction Tests
# =============================================================================

def test_debugger_default_disabled():
    """
        Test that the debugger is disabled by default (opt-in activation).
    """
    debugger = InteractiveDebugger(pin="1234")

    if debugger.enabled is not False:
        errmsg = "Expected debugger to be disabled by default"
        raise AssertionError(errmsg)

    return


def test_debugger_enabled_construction():
    """
        Test that the debugger can be explicitly enabled.
    """
    debugger = InteractiveDebugger(pin="secret", timeout=600, enabled=True)

    if debugger.enabled is not True:
        errmsg = "Expected debugger to be enabled"
        raise AssertionError(errmsg)

    if debugger.pin != "secret":
        errmsg = "Expected pin 'secret', got '{}'".format(debugger.pin)
        raise AssertionError(errmsg)

    if debugger.timeout != 600:
        errmsg = "Expected timeout 600, got {}".format(debugger.timeout)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Opt-in Activation Tests
# =============================================================================

def test_create_session_fails_when_disabled():
    """
        Test that creating a session raises RuntimeError when the
        debugger is not enabled.
    """
    debugger = InteractiveDebugger(pin="1234", enabled=False)
    frames = _make_frames()
    exception = _make_exception()

    raised = False
    try:
        debugger.create_session(exception, frames)
    except RuntimeError:
        raised = True

    if raised is not True:
        errmsg = "Expected RuntimeError when creating session on disabled debugger"
        raise AssertionError(errmsg)

    return


# =============================================================================
# PIN Security Tests
# =============================================================================

def test_evaluate_rejects_wrong_pin():
    """
        Test that evaluate returns an error for an incorrect PIN.
    """
    debugger = InteractiveDebugger(pin="correct-pin", enabled=True)
    frames = _make_frames()
    frame_locals = _make_frame_locals()
    exception = _make_exception()

    session_id = debugger.create_session(exception, frames, frame_locals)

    result = debugger.evaluate(
        session_id=session_id,
        frame_index=0,
        expression="1 + 1",
        pin="wrong-pin",
    )

    if "error" not in result:
        errmsg = "Expected error in result for wrong PIN"
        raise AssertionError(errmsg)

    if result["error"] != INVALID_PIN_MESSAGE:
        errmsg = "Expected '{}', got '{}'".format(
            INVALID_PIN_MESSAGE, result["error"],
        )
        raise AssertionError(errmsg)

    return


def test_evaluate_accepts_correct_pin():
    """
        Test that evaluate works with the correct PIN.
    """
    debugger = InteractiveDebugger(pin="my-pin", enabled=True)
    frames = _make_frames()
    frame_locals = [{"a": 5, "b": 10}]
    exception = _make_exception()

    session_id = debugger.create_session(exception, frames, frame_locals)

    result = debugger.evaluate(
        session_id=session_id,
        frame_index=0,
        expression="a + b",
        pin="my-pin",
    )

    if "error" in result:
        errmsg = "Unexpected error: {}".format(result["error"])
        raise AssertionError(errmsg)

    if result["result"] != "15":
        errmsg = "Expected result '15', got '{}'".format(result["result"])
        raise AssertionError(errmsg)

    return


def test_get_frames_rejects_wrong_pin():
    """
        Test that get_frames returns an error for an incorrect PIN.
    """
    debugger = InteractiveDebugger(pin="pin123", enabled=True)
    frames = _make_frames()
    exception = _make_exception()

    session_id = debugger.create_session(exception, frames)

    result = debugger.get_frames(session_id=session_id, pin="wrong")

    if "error" not in result:
        errmsg = "Expected error in result for wrong PIN"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Expression Evaluation Tests
# =============================================================================

def test_evaluate_expression_in_frame_context():
    """
        Test that expressions are evaluated using the frame's local
        variables.
    """
    debugger = InteractiveDebugger(pin="pin", enabled=True)
    frames = _make_frames(count=2)
    frame_locals = [
        {"x": 100, "y": 200},
        {"x": 1, "y": 2},
    ]
    exception = _make_exception()

    session_id = debugger.create_session(exception, frames, frame_locals)

    # Evaluate in frame 0
    result_0 = debugger.evaluate(
        session_id=session_id,
        frame_index=0,
        expression="x + y",
        pin="pin",
    )

    if result_0["result"] != "300":
        errmsg = "Expected '300' for frame 0, got '{}'".format(result_0["result"])
        raise AssertionError(errmsg)

    # Evaluate in frame 1
    result_1 = debugger.evaluate(
        session_id=session_id,
        frame_index=1,
        expression="x + y",
        pin="pin",
    )

    if result_1["result"] != "3":
        errmsg = "Expected '3' for frame 1, got '{}'".format(result_1["result"])
        raise AssertionError(errmsg)

    return


def test_evaluate_invalid_expression():
    """
        Test that invalid expressions return an error result.
    """
    debugger = InteractiveDebugger(pin="pin", enabled=True)
    frames = _make_frames(count=1)
    frame_locals = [{"x": 10}]
    exception = _make_exception()

    session_id = debugger.create_session(exception, frames, frame_locals)

    result = debugger.evaluate(
        session_id=session_id,
        frame_index=0,
        expression="undefined_var",
        pin="pin",
    )

    if "error" not in result:
        errmsg = "Expected error for undefined variable expression"
        raise AssertionError(errmsg)

    return


def test_evaluate_returns_repr():
    """
        Test that evaluate returns the repr of the result.
    """
    debugger = InteractiveDebugger(pin="pin", enabled=True)
    frames = _make_frames(count=1)
    frame_locals = [{"msg": "hello world"}]
    exception = _make_exception()

    session_id = debugger.create_session(exception, frames, frame_locals)

    result = debugger.evaluate(
        session_id=session_id,
        frame_index=0,
        expression="msg",
        pin="pin",
    )

    if result["result"] != "'hello world'":
        errmsg = "Expected \"'hello world'\", got '{}'".format(result["result"])
        raise AssertionError(errmsg)

    return


# =============================================================================
# Stack Frame Navigation Tests
# =============================================================================

def test_get_frames_returns_all_frames():
    """
        Test that get_frames returns information about all stack frames.
    """
    debugger = InteractiveDebugger(pin="pin", enabled=True)
    frames = _make_frames(count=4)
    exception = _make_exception()

    session_id = debugger.create_session(exception, frames)

    result = debugger.get_frames(session_id=session_id, pin="pin")

    if "frames" not in result:
        errmsg = "Expected 'frames' key in result"
        raise AssertionError(errmsg)

    if len(result["frames"]) != 4:
        errmsg = "Expected 4 frames, got {}".format(len(result["frames"]))
        raise AssertionError(errmsg)

    # Verify frame indices
    for idx, frame_data in enumerate(result["frames"]):
        if frame_data["index"] != idx:
            errmsg = "Expected frame index {}, got {}".format(
                idx, frame_data["index"],
            )
            raise AssertionError(errmsg)

    return


def test_evaluate_out_of_range_frame():
    """
        Test that evaluating with an out-of-range frame index returns
        an error.
    """
    debugger = InteractiveDebugger(pin="pin", enabled=True)
    frames = _make_frames(count=2)
    frame_locals = _make_frame_locals(count=2)
    exception = _make_exception()

    session_id = debugger.create_session(exception, frames, frame_locals)

    result = debugger.evaluate(
        session_id=session_id,
        frame_index=5,
        expression="1 + 1",
        pin="pin",
    )

    if "error" not in result:
        errmsg = "Expected error for out-of-range frame index"
        raise AssertionError(errmsg)

    if result["error"] != FRAME_INDEX_OUT_OF_RANGE_MESSAGE:
        errmsg = "Expected '{}', got '{}'".format(
            FRAME_INDEX_OUT_OF_RANGE_MESSAGE, result["error"],
        )
        raise AssertionError(errmsg)

    return


def test_evaluate_negative_frame_index():
    """
        Test that evaluating with a negative frame index returns an error.
    """
    debugger = InteractiveDebugger(pin="pin", enabled=True)
    frames = _make_frames(count=2)
    frame_locals = _make_frame_locals(count=2)
    exception = _make_exception()

    session_id = debugger.create_session(exception, frames, frame_locals)

    result = debugger.evaluate(
        session_id=session_id,
        frame_index=-1,
        expression="1 + 1",
        pin="pin",
    )

    if "error" not in result:
        errmsg = "Expected error for negative frame index"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Session Timeout Tests
# =============================================================================

def test_session_expires_after_timeout():
    """
        Test that sessions are cleaned up after the timeout period.
    """
    debugger = InteractiveDebugger(pin="pin", timeout=1, enabled=True)
    frames = _make_frames(count=1)
    exception = _make_exception()

    session_id = debugger.create_session(exception, frames)

    if debugger.session_count != 1:
        errmsg = "Expected 1 session, got {}".format(debugger.session_count)
        raise AssertionError(errmsg)

    # Wait for timeout
    time.sleep(1.1)

    # Trigger cleanup via get_session
    session = debugger.get_session(session_id)

    if session is not None:
        errmsg = "Expected session to be expired and None"
        raise AssertionError(errmsg)

    if debugger.session_count != 0:
        errmsg = "Expected 0 sessions after timeout, got {}".format(
            debugger.session_count,
        )
        raise AssertionError(errmsg)

    return


def test_session_not_expired_before_timeout():
    """
        Test that sessions remain active before the timeout period.
    """
    debugger = InteractiveDebugger(pin="pin", timeout=60, enabled=True)
    frames = _make_frames(count=1)
    exception = _make_exception()

    session_id = debugger.create_session(exception, frames)

    session = debugger.get_session(session_id)

    if session is None:
        errmsg = "Expected session to still be active"
        raise AssertionError(errmsg)

    return


def test_evaluate_expired_session():
    """
        Test that evaluating on an expired session returns an error.
    """
    debugger = InteractiveDebugger(pin="pin", timeout=1, enabled=True)
    frames = _make_frames(count=1)
    frame_locals = [{"x": 1}]
    exception = _make_exception()

    session_id = debugger.create_session(exception, frames, frame_locals)

    # Wait for timeout
    time.sleep(1.1)

    result = debugger.evaluate(
        session_id=session_id,
        frame_index=0,
        expression="x",
        pin="pin",
    )

    if "error" not in result:
        errmsg = "Expected error for expired session"
        raise AssertionError(errmsg)

    if result["error"] != SESSION_NOT_FOUND_MESSAGE:
        errmsg = "Expected '{}', got '{}'".format(
            SESSION_NOT_FOUND_MESSAGE, result["error"],
        )
        raise AssertionError(errmsg)

    return


def test_activity_resets_timeout():
    """
        Test that activity on a session resets the timeout clock.
    """
    debugger = InteractiveDebugger(pin="pin", timeout=2, enabled=True)
    frames = _make_frames(count=1)
    frame_locals = [{"x": 42}]
    exception = _make_exception()

    session_id = debugger.create_session(exception, frames, frame_locals)

    # Wait 1 second, then evaluate (should reset timeout)
    time.sleep(1.0)
    result = debugger.evaluate(
        session_id=session_id,
        frame_index=0,
        expression="x",
        pin="pin",
    )

    if "error" in result:
        errmsg = "Unexpected error after activity: {}".format(result["error"])
        raise AssertionError(errmsg)

    # Wait another 1 second (total 2 from start, but only 1 from last activity)
    time.sleep(1.0)
    session = debugger.get_session(session_id)

    if session is None:
        errmsg = "Expected session to still be active after activity reset"
        raise AssertionError(errmsg)

    return
