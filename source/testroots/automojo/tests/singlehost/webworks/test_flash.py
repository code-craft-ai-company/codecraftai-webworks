"""
    Unit tests for the flash-message module.

    Covers:
        - InMemoryFlashStore add/consume_all/peek_all semantics.
        - FlashManager input validation, category defaulting, and
          delegation to the configured store.
        - make_flash_context_processor injection and consumption
          behaviours.
"""

from typing import List, Tuple

from automojo.webworks.flash import (
    FlashError,
    FlashManager,
    FlashStore,
    InMemoryFlashStore,
    make_flash_context_processor,
)


SESSION_ID = "session-flash-001"
OTHER_SESSION_ID = "session-flash-002"


# =============================================================================
# Test Helpers
# =============================================================================

class RecordingFlashStore(FlashStore):
    """
        Captures every call so tests can verify FlashManager delegates
        through to its store correctly.
    """

    def __init__(self) -> None:
        self.add_calls: List[Tuple[str, str, str]] = []
        self.consume_calls: List[str] = []
        self.peek_calls: List[str] = []
        self._messages: List[Tuple[str, str]] = []

    def add(self, session_id: str, category: str, message: str) -> None:
        self.add_calls.append((session_id, category, message))
        self._messages.append((category, message))
        return

    def consume_all(self, session_id: str):
        self.consume_calls.append(session_id)
        result = list(self._messages)
        self._messages = []
        return result

    def peek_all(self, session_id: str):
        self.peek_calls.append(session_id)
        return list(self._messages)


# =============================================================================
# InMemoryFlashStore
# =============================================================================

def test_in_memory_store_consume_returns_empty_when_no_messages():
    """
        consume_all on a session with no pending messages returns an
        empty list — not an error.
    """
    store = InMemoryFlashStore()

    result = store.consume_all(SESSION_ID)

    if result != []:
        errmsg = "Expected empty list, got {!r}".format(result)
        raise AssertionError(errmsg)

    return


def test_in_memory_store_add_and_consume_preserves_order():
    """
        Messages added in sequence are returned in insertion order.
    """
    store = InMemoryFlashStore()

    store.add(SESSION_ID, "info", "first")
    store.add(SESSION_ID, "warning", "second")
    store.add(SESSION_ID, "success", "third")

    result = store.consume_all(SESSION_ID)
    expected = [
        ("info", "first"),
        ("warning", "second"),
        ("success", "third"),
    ]

    if result != expected:
        errmsg = "Expected {!r}, got {!r}".format(expected, result)
        raise AssertionError(errmsg)

    return


def test_in_memory_store_consume_clears_messages():
    """
        Once consumed, messages are removed; a second consume returns
        an empty list.
    """
    store = InMemoryFlashStore()
    store.add(SESSION_ID, "info", "one")
    store.add(SESSION_ID, "info", "two")

    first = store.consume_all(SESSION_ID)
    second = store.consume_all(SESSION_ID)

    if len(first) != 2:
        errmsg = "Expected 2 messages on first consume, got {}".format(len(first))
        raise AssertionError(errmsg)

    if second != []:
        errmsg = "Expected no messages on second consume, got {!r}".format(second)
        raise AssertionError(errmsg)

    return


def test_in_memory_store_peek_does_not_clear():
    """
        peek_all returns the same messages on repeated calls without
        modifying the store.
    """
    store = InMemoryFlashStore()
    store.add(SESSION_ID, "info", "one")
    store.add(SESSION_ID, "info", "two")

    first = store.peek_all(SESSION_ID)
    second = store.peek_all(SESSION_ID)

    if first != second:
        errmsg = "Expected peeks to be equal, got {!r} vs {!r}".format(first, second)
        raise AssertionError(errmsg)

    if len(first) != 2:
        errmsg = "Expected peek to return 2 messages, got {}".format(len(first))
        raise AssertionError(errmsg)

    return


def test_in_memory_store_isolates_sessions():
    """
        Messages added under one session id are not visible to another.
    """
    store = InMemoryFlashStore()
    store.add(SESSION_ID, "info", "for first")
    store.add(OTHER_SESSION_ID, "error", "for second")

    first_messages = store.consume_all(SESSION_ID)
    second_messages = store.consume_all(OTHER_SESSION_ID)

    if first_messages != [("info", "for first")]:
        errmsg = "Unexpected messages for SESSION_ID: {!r}".format(first_messages)
        raise AssertionError(errmsg)

    if second_messages != [("error", "for second")]:
        errmsg = "Unexpected messages for OTHER_SESSION_ID: {!r}".format(second_messages)
        raise AssertionError(errmsg)

    return


def test_in_memory_store_consume_returns_independent_list():
    """
        Mutating the list returned by consume_all must not affect future
        store state. Defends against accidental aliasing of internals.
    """
    store = InMemoryFlashStore()
    store.add(SESSION_ID, "info", "one")

    returned = store.consume_all(SESSION_ID)
    returned.append(("info", "leaked"))

    second = store.consume_all(SESSION_ID)
    if second != []:
        errmsg = "Expected empty list, got {!r}".format(second)
        raise AssertionError(errmsg)

    return


# =============================================================================
# FlashManager
# =============================================================================

def test_manager_uses_in_memory_store_by_default():
    """
        Constructing a manager without a store should pick up
        InMemoryFlashStore so callers can use it out of the box.
    """
    manager = FlashManager()

    if not isinstance(manager.store, InMemoryFlashStore):
        errmsg = "Expected InMemoryFlashStore default, got {!r}".format(type(manager.store))
        raise AssertionError(errmsg)

    return


def test_manager_add_default_category():
    """
        manager.add without a category uses the configured default.
    """
    store = RecordingFlashStore()
    manager = FlashManager(store=store, default_category="notice")

    manager.add(session_id=SESSION_ID, message="hello")

    if len(store.add_calls) != 1:
        errmsg = "Expected exactly one add call, got {}".format(len(store.add_calls))
        raise AssertionError(errmsg)

    actual_session, actual_category, actual_message = store.add_calls[0]

    if actual_category != "notice":
        errmsg = "Expected default category 'notice', got {!r}".format(actual_category)
        raise AssertionError(errmsg)

    if actual_message != "hello":
        errmsg = "Expected message 'hello', got {!r}".format(actual_message)
        raise AssertionError(errmsg)

    if actual_session != SESSION_ID:
        errmsg = "Expected session_id {!r}, got {!r}".format(SESSION_ID, actual_session)
        raise AssertionError(errmsg)

    return


def test_manager_add_explicit_category_overrides_default():
    """
        Explicit category passed to add() overrides default_category.
    """
    store = RecordingFlashStore()
    manager = FlashManager(store=store, default_category="info")

    manager.add(session_id=SESSION_ID, message="boom", category="error")

    _session, category, _message = store.add_calls[0]
    if category != "error":
        errmsg = "Expected category 'error', got {!r}".format(category)
        raise AssertionError(errmsg)

    return


def test_manager_add_empty_category_falls_back_to_default():
    """
        A whitespace-only category falls back to the default rather than
        being recorded as an empty string.
    """
    store = RecordingFlashStore()
    manager = FlashManager(store=store, default_category="info")

    manager.add(session_id=SESSION_ID, message="x", category="   ")

    _session, category, _message = store.add_calls[0]
    if category != "info":
        errmsg = "Expected fallback to 'info', got {!r}".format(category)
        raise AssertionError(errmsg)

    return


def test_manager_rejects_empty_session_id():
    """
        add() with an empty session id raises FlashError. Treats it as
        a programming error rather than silently dropping the message.
    """
    manager = FlashManager()

    try:
        manager.add(session_id="", message="hi")
    except FlashError:
        return

    errmsg = "Expected FlashError for empty session_id"
    raise AssertionError(errmsg)


def test_manager_rejects_empty_message():
    """
        add() with an empty message raises FlashError.
    """
    manager = FlashManager()

    try:
        manager.add(session_id=SESSION_ID, message="")
    except FlashError:
        return

    errmsg = "Expected FlashError for empty message"
    raise AssertionError(errmsg)


def test_manager_consume_all_returns_empty_for_invalid_session_id():
    """
        consume_all with None or empty session id yields an empty list,
        not an error — read paths should be lenient.
    """
    manager = FlashManager()

    if manager.consume_all(None) != []:
        raise AssertionError("Expected [] for None session_id")
    if manager.consume_all("") != []:
        raise AssertionError("Expected [] for empty session_id")

    return


def test_manager_consume_all_round_trips_through_store():
    """
        Adding and consuming via the manager round-trips through the
        underlying store.
    """
    manager = FlashManager()

    manager.add(session_id=SESSION_ID, message="m1", category="info")
    manager.add(session_id=SESSION_ID, message="m2", category="error")

    messages = manager.consume_all(SESSION_ID)
    expected = [("info", "m1"), ("error", "m2")]

    if messages != expected:
        errmsg = "Expected {!r}, got {!r}".format(expected, messages)
        raise AssertionError(errmsg)

    return


# =============================================================================
# make_flash_context_processor
# =============================================================================

def test_context_processor_consumes_messages_by_default():
    """
        Default behaviour drains the store: subsequent renders see no
        messages, matching the classic Flask flash() lifecycle.
    """
    manager = FlashManager()
    manager.add(session_id=SESSION_ID, message="saved", category="success")

    processor = make_flash_context_processor(manager)

    first = processor({"session_id": SESSION_ID})
    second = processor({"session_id": SESSION_ID})

    if first.get("flash_messages") != [("success", "saved")]:
        errmsg = "First render did not return the message: {!r}".format(first)
        raise AssertionError(errmsg)

    if second.get("flash_messages") != []:
        errmsg = "Expected empty messages on second render, got {!r}".format(second)
        raise AssertionError(errmsg)

    return


def test_context_processor_peek_mode_does_not_clear():
    """
        With consume=False the processor peeks, so two renders see the
        same set of pending messages.
    """
    manager = FlashManager()
    manager.add(session_id=SESSION_ID, message="hello", category="info")

    processor = make_flash_context_processor(manager, consume=False)

    first = processor({"session_id": SESSION_ID})
    second = processor({"session_id": SESSION_ID})

    if first != second:
        errmsg = "Peek mode rendered different results: {!r} vs {!r}".format(first, second)
        raise AssertionError(errmsg)

    if len(first.get("flash_messages") or []) != 1:
        errmsg = "Expected 1 message in peek mode, got {!r}".format(first)
        raise AssertionError(errmsg)

    return


def test_context_processor_returns_empty_when_no_session_id():
    """
        Anonymous renders (no session_id in context) get nothing; this
        protects against accidentally exposing messages from a stale or
        unrelated session.
    """
    manager = FlashManager()
    manager.add(session_id=SESSION_ID, message="should not leak", category="info")

    processor = make_flash_context_processor(manager)

    output = processor({})

    if output != {}:
        errmsg = "Expected empty dict for anonymous render, got {!r}".format(output)
        raise AssertionError(errmsg)

    # And confirm the message stays in the store for the real session.
    leftover = manager.peek_all(SESSION_ID)
    if len(leftover) != 1:
        errmsg = "Anonymous render must not have consumed real-session messages"
        raise AssertionError(errmsg)

    return


def test_context_processor_uses_configured_keys():
    """
        Custom session_id_key / messages_key flow through end-to-end.
    """
    manager = FlashManager()
    manager.add(session_id=SESSION_ID, message="hi", category="info")

    processor = make_flash_context_processor(
        manager,
        session_id_key="sid",
        messages_key="banner",
    )

    output = processor({"sid": SESSION_ID})

    if "banner" not in output:
        errmsg = "Expected 'banner' key in processor output, got {!r}".format(output)
        raise AssertionError(errmsg)

    if output["banner"] != [("info", "hi")]:
        errmsg = "Unexpected banner contents: {!r}".format(output["banner"])
        raise AssertionError(errmsg)

    return
