"""
.. module:: flash
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Flash-message store, manager, and templating context processor
        for one-shot user feedback messages.

.. moduleauthor:: Code Craft AI LLC

A flash message is a short, one-shot piece of user feedback (success
banner, error notice, validation tip) emitted by one HTTP handler and
consumed on the next render. The classic use case is a POST/redirect/GET
flow: the POST handler validates a form, calls
``flash_manager.add(session_id, "Saved!", "success")``, and redirects;
the next GET handler renders a template that pulls the message via the
context processor and clears it from the store.

Components:

    - :class:`FlashStore` — abstract base class for persistence backends.
      Subclass to plug in Redis, SQL, or any other shared store.
    - :class:`InMemoryFlashStore` — process-local default. Sufficient for
      single-process development; production deployments behind multiple
      workers should swap in a shared backend.
    - :class:`FlashManager` — facade that resolves backend lookups and
      adds light validation. Sibling handlers depend on the manager
      rather than the store directly.
    - :func:`make_flash_context_processor` — factory returning a context
      processor compatible with
      :class:`ccai.webworks.templating.context.ContextProcessorRegistry`.

Categorization
--------------

Each message carries a *category* string that the rendering layer can
key on for styling (``info``, ``success``, ``warning``, ``error``).
Categories are free-form strings; downstream UI conventions decide
which ones are recognized. The default category is ``"info"``.

Lifecycle
---------

Messages are *consumed* by default — when the context processor reads
them out of the store they are removed, so a subsequent render does not
duplicate them. Subclasses that want a "peek without clear" pass
through the store's :meth:`peek_all` method.

Bounds
------

The in-memory store is bounded so that messages nobody ever reads -- an
abandoned login, a client that drops the redirect, session ids rotated by
an attacker -- cannot grow the process without limit. A message expires
after :data:`DEFAULT_FLASH_TTL_SECONDS`; a session keeps at most
:data:`DEFAULT_MAX_MESSAGES_PER_SESSION` messages and the store at most
:data:`DEFAULT_MAX_SESSIONS` sessions, the oldest being dropped to make
room; and a message longer than :data:`DEFAULT_MAX_MESSAGE_LENGTH`
characters is cut short. Every limit can be changed when the store is
constructed.

Concurrency
-----------

The in-memory store uses a per-session list and is intended for the
single-process common case. Multi-worker deployments must use a backend
that is consistent across workers (Redis, database, etc.). The
abstract :class:`FlashStore` interface is intentionally tiny so swapping
in a real backend is a small implementation exercise.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import collections
import threading
import time

from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple


DEFAULT_FLASH_CATEGORY = "info"

# Limits applied by :class:`InMemoryFlashStore` unless overridden.

#: Seconds a message stays in the store when it is not read.
DEFAULT_FLASH_TTL_SECONDS = 3600.0

#: Messages kept for one session; the oldest is dropped to admit a new one.
DEFAULT_MAX_MESSAGES_PER_SESSION = 32

#: Sessions kept in the store; the one idle longest is dropped to admit a
#: new one.
DEFAULT_MAX_SESSIONS = 10000

#: Characters kept of a message, and of a category.
DEFAULT_MAX_MESSAGE_LENGTH = 2000
DEFAULT_MAX_CATEGORY_LENGTH = 64

# Appended to a message that was cut to the length limit.
TRUNCATION_MARK = "..."

# A single flash message is represented as a (category, message) tuple.
# The list returned to templates preserves insertion order so the UI can
# render messages in the sequence they were added.
FlashMessage = Tuple[str, str]


class FlashError(Exception):
    """
        Raised when flash-message inputs are invalid in a way the caller
        should treat as a programming error (empty session id, non-string
        message, etc.).

        Routine "no messages for this session" results from a consume
        call return an empty list rather than raising.
    """

    pass


class FlashStore:
    """
        Abstract base class for flash-message persistence backends.

        Subclasses implement three operations:

            - :meth:`add` — append a message for a session.
            - :meth:`consume_all` — return every pending message for a
              session and remove them from the store atomically.
            - :meth:`peek_all` — return every pending message for a
              session without modifying the store. Optional helper for
              previewing in admin tools or tests.

        The default :class:`FlashManager` uses :class:`InMemoryFlashStore`
        when no store is supplied.
    """

    def add(self, session_id: str, category: str, message: str) -> None:
        """
            Append a message to the store for a session.

            :param session_id: Identifier of the session the message
                               belongs to.
            :param category: Free-form category string (e.g. ``"info"``,
                             ``"error"``).
            :param message: Plain-text message body.
        """
        raise NotImplementedError("Subclasses must implement add")

    def consume_all(self, session_id: str) -> List[FlashMessage]:
        """
            Return and remove all pending messages for a session.

            :param session_id: Identifier of the session whose messages
                               should be consumed.

            :returns: List of ``(category, message)`` tuples in insertion
                      order. Empty list when no messages are pending.
        """
        raise NotImplementedError("Subclasses must implement consume_all")

    def peek_all(self, session_id: str) -> List[FlashMessage]:
        """
            Return all pending messages for a session without removing them.

            :param session_id: Identifier of the session whose messages
                               should be returned.

            :returns: List of ``(category, message)`` tuples. Empty list
                      when no messages are pending.
        """
        raise NotImplementedError("Subclasses must implement peek_all")


class InMemoryFlashStore(FlashStore):
    """
        Process-local in-memory flash store.

        Suitable for single-process development and testing. Multi-worker
        deployments must swap in a shared backend (Redis, database, etc.).

        The store guards its internal mapping with a lock so concurrent
        threads adding messages for the same session do not interleave
        list mutations. The lock does *not* protect against multi-process
        races; that's the deployment's responsibility.

        The store is bounded. Messages leave it when their session reads
        them, and also when they expire, when their session holds more than
        its share, or when the store holds too many sessions -- so a session
        that never renders again cannot hold memory forever.

        :param ttl_seconds: Seconds an unread message is kept. ``None``
                            disables expiry.
        :param max_messages_per_session: Messages kept for one session.
                                         Adding one more drops the oldest.
        :param max_sessions: Sessions kept. Adding a message for one more
                             drops the session that has gone longest
                             without a new message.
        :param max_message_length: Characters kept of a message; a longer
                                   one is cut and marked with ``...``.
        :param max_category_length: Characters kept of a category.
        :param time_source: Callable returning the current time in seconds,
                            as :func:`time.monotonic` does. For tests.

        :raises FlashError: When a limit is not a positive number.
    """

    def __init__(
        self,
        ttl_seconds: Optional[float] = DEFAULT_FLASH_TTL_SECONDS,
        max_messages_per_session: int = DEFAULT_MAX_MESSAGES_PER_SESSION,
        max_sessions: int = DEFAULT_MAX_SESSIONS,
        max_message_length: int = DEFAULT_MAX_MESSAGE_LENGTH,
        max_category_length: int = DEFAULT_MAX_CATEGORY_LENGTH,
        time_source: Optional[Callable[[], float]] = None
    ) -> None:
        """
            Construct an empty in-memory store.

            :param ttl_seconds: Seconds an unread message is kept, or
                                ``None`` for no expiry.
            :param max_messages_per_session: Messages kept for one session.
            :param max_sessions: Sessions kept.
            :param max_message_length: Characters kept of a message.
            :param max_category_length: Characters kept of a category.
            :param time_source: Callable returning the current time in
                                seconds. Defaults to :func:`time.monotonic`.

            :raises FlashError: When a limit is not a positive number.
        """
        if ttl_seconds is not None and ttl_seconds <= 0:
            raise FlashError("ttl_seconds must be greater than zero, or None")

        limits = {
            "max_messages_per_session": max_messages_per_session,
            "max_sessions": max_sessions,
            "max_message_length": max_message_length,
            "max_category_length": max_category_length,
        }
        for limit_name, limit_value in limits.items():
            if not isinstance(limit_value, int) or isinstance(limit_value, bool) or limit_value < 1:
                raise FlashError("{} must be an integer of at least 1".format(limit_name))

        self._ttl_seconds = ttl_seconds
        self._max_messages_per_session = max_messages_per_session
        self._max_sessions = max_sessions
        self._max_message_length = max_message_length
        self._max_category_length = max_category_length
        self._time_source: Callable[[], float] = time_source if time_source is not None else time.monotonic

        # Session id -> [(added_at, category, message), ...], oldest first.
        # The mapping is kept in order of each session's latest addition,
        # so the first entry is always the session idle longest.
        self._messages: "collections.OrderedDict[str, List[Tuple[float, str, str]]]" = collections.OrderedDict()
        self._lock = threading.RLock()
        return

    def add(self, session_id: str, category: str, message: str) -> None:
        """
            Append a message for the given session.

            The message and category are cut to the store's length limits,
            expired messages are discarded, and the oldest message of the
            session -- or the session idle longest -- is dropped when a
            limit would otherwise be exceeded.

            :param session_id: Identifier of the target session.
            :param category: Category string.
            :param message: Plain-text message body.
        """
        stored_category = self._truncate(category, self._max_category_length, mark="")
        stored_message = self._truncate(message, self._max_message_length, mark=TRUNCATION_MARK)

        with self._lock:
            now = self._time_source()
            self._discard_expired(now)

            pending = self._messages.get(session_id)
            if pending is None:
                # Make room for the new session by dropping the ones that
                # have gone longest without a message.
                while len(self._messages) >= self._max_sessions:
                    self._messages.popitem(last=False)
                pending = []
                self._messages[session_id] = pending
            else:
                self._messages.move_to_end(session_id)

            pending.append((now, stored_category, stored_message))

            while len(pending) > self._max_messages_per_session:
                pending.pop(0)

        return

    def consume_all(self, session_id: str) -> List[FlashMessage]:
        """
            Return and remove all pending messages for the given session.

            :param session_id: Identifier of the target session.

            :returns: List of ``(category, message)`` tuples in insertion
                      order. Expired messages are not returned.
        """
        with self._lock:
            now = self._time_source()
            pending = self._messages.pop(session_id, None)
            self._discard_expired(now)

        if pending is None:
            return []

        # Return a fresh list so callers cannot mutate internal state.
        rtnval = self._live_messages(pending, now)
        return rtnval

    def peek_all(self, session_id: str) -> List[FlashMessage]:
        """
            Return all pending messages for the given session without
            removing them.

            :param session_id: Identifier of the target session.

            :returns: List of ``(category, message)`` tuples in insertion
                      order. Expired messages are not returned.
        """
        with self._lock:
            now = self._time_source()
            pending = self._messages.get(session_id)
            if pending is None:
                return []
            rtnval = self._live_messages(pending, now)
        return rtnval

    def session_count(self) -> int:
        """
            The number of sessions that currently hold messages.

            :returns: The session count.
        """
        with self._lock:
            rtnval = len(self._messages)
        return rtnval

    def _is_expired(self, added_at: float, now: float) -> bool:
        """
            Whether a message added at ``added_at`` has outlived the TTL.

            :param added_at: When the message was added.
            :param now: The current time from the store's time source.

            :returns: True when the message has expired.
        """
        if self._ttl_seconds is None:
            return False

        rtnval = (now - added_at) >= self._ttl_seconds
        return rtnval

    def _live_messages(self, pending: List[Tuple[float, str, str]], now: float) -> List[FlashMessage]:
        """
            The messages of a session that have not expired.

            :param pending: The stored entries of one session.
            :param now: The current time from the store's time source.

            :returns: List of ``(category, message)`` tuples, oldest first.
        """
        rtnval: List[FlashMessage] = []
        for added_at, category, message in pending:
            if self._is_expired(added_at, now):
                continue
            rtnval.append((category, message))
        return rtnval

    def _discard_expired(self, now: float) -> None:
        """
            Remove the sessions whose every message has expired. The caller
            holds the lock.

            Sessions are ordered by their latest addition, so the scan stops
            at the first session that still has a live message: every
            session after it received a message more recently.

            :param now: The current time from the store's time source.
        """
        if self._ttl_seconds is None:
            return

        while len(self._messages) > 0:
            oldest_session_id = next(iter(self._messages))
            pending = self._messages[oldest_session_id]
            latest_added_at = pending[-1][0] if len(pending) > 0 else None
            if latest_added_at is not None and not self._is_expired(latest_added_at, now):
                break
            del self._messages[oldest_session_id]

        return

    @staticmethod
    def _truncate(text: str, limit: int, mark: str) -> str:
        """
            Cut text to a length limit.

            :param text: The text to bound.
            :param limit: The most characters to keep, mark included.
            :param mark: Text appended to show that a cut was made.

            :returns: ``text`` when it fits, otherwise its beginning followed
                      by ``mark``, ``limit`` characters in all.
        """
        if len(text) <= limit:
            return text

        keep = limit - len(mark)
        if keep < 0:
            keep = limit
            mark = ""

        rtnval = text[:keep] + mark
        return rtnval


class FlashManager:
    """
        Facade in front of a :class:`FlashStore` that adds input
        validation and category defaulting.

        Handlers depend on this manager rather than on the store directly,
        so swapping the backing store does not change call sites. The
        manager validates that ``session_id`` and ``message`` are non-empty
        strings and applies a default category when one is not supplied.

        :param store: Backing :class:`FlashStore`. When ``None``, a fresh
                      :class:`InMemoryFlashStore` is used.
        :param default_category: Category applied when :meth:`add` is
                                 called without an explicit category.
    """

    def __init__(
        self,
        store: Optional[FlashStore] = None,
        default_category: str = DEFAULT_FLASH_CATEGORY
    ) -> None:
        """
            Construct a flash manager bound to a store.

            :param store: Backing store. When ``None`` an in-memory store
                          is used.
            :param default_category: Default category for :meth:`add`
                                     when no explicit category is given.
        """
        if store is None:
            self._store = InMemoryFlashStore()
        else:
            self._store = store

        self._default_category = str(default_category or DEFAULT_FLASH_CATEGORY)
        return

    @property
    def store(self) -> FlashStore:
        """
            The backing store this manager delegates to.

            :returns: The :class:`FlashStore` instance.
        """
        return self._store

    @property
    def default_category(self) -> str:
        """
            Category applied by :meth:`add` when no explicit category
            is provided.

            :returns: The default category string.
        """
        return self._default_category

    def add(
        self,
        session_id: str,
        message: str,
        category: Optional[str] = None
    ) -> None:
        """
            Add a flash message for a session.

            :param session_id: Identifier of the target session.
            :param message: Plain-text message body. Must be a non-empty
                            string.
            :param category: Optional category string. Defaults to
                             :attr:`default_category` when omitted or
                             empty.

            :raises FlashError: When ``session_id`` or ``message`` is
                                empty or not a string.
        """
        if session_id is None or not isinstance(session_id, str):
            raise FlashError("session_id must be a string")
        if len(session_id) == 0:
            raise FlashError("session_id must not be empty")

        if message is None or not isinstance(message, str):
            raise FlashError("message must be a string")
        if len(message) == 0:
            raise FlashError("message must not be empty")

        if category is None:
            resolved_category = self._default_category
        else:
            stripped_category = str(category).strip()
            if len(stripped_category) == 0:
                resolved_category = self._default_category
            else:
                resolved_category = stripped_category

        self._store.add(
            session_id=session_id,
            category=resolved_category,
            message=message
        )
        return

    def consume_all(self, session_id: str) -> List[FlashMessage]:
        """
            Return and remove all pending messages for a session.

            :param session_id: Identifier of the target session.

            :returns: List of ``(category, message)`` tuples in insertion
                      order. Empty list when no session id is supplied or
                      no messages are pending.
        """
        if session_id is None or not isinstance(session_id, str):
            return []
        if len(session_id) == 0:
            return []

        rtnval = self._store.consume_all(session_id)
        return rtnval

    def peek_all(self, session_id: str) -> List[FlashMessage]:
        """
            Return all pending messages for a session without removing
            them.

            :param session_id: Identifier of the target session.

            :returns: List of ``(category, message)`` tuples in insertion
                      order. Empty list when no session id is supplied or
                      no messages are pending.
        """
        if session_id is None or not isinstance(session_id, str):
            return []
        if len(session_id) == 0:
            return []

        rtnval = self._store.peek_all(session_id)
        return rtnval


class LazyFlashMessages(list):
    """
        The pending flash messages of one session, read from the store only
        when something actually looks at them.

        The flash context processor runs for every render that knows the
        session, including ones that never show a message -- an error page,
        an HTML fragment, an email. Reading the store there and then drained
        the queue, and the page meant to show the message found it empty.
        This object is what the processor injects instead. It is the list of
        ``(category, message)`` tuples, filled in late: iterating it,
        indexing it, taking its length or its truth value, or comparing it
        to a list reads the messages, once, and keeps them for the rest of
        the render. A render that never touches it leaves the store alone.

        It is a ``list`` so that code which expects one -- a template that
        writes ``flash_messages.0``, say -- keeps working. It is also
        callable, returning a plain list, so a template engine that calls
        what it finds in the context hands the template an ordinary list.

        :param manager: Manager whose store the messages are read from.
        :param session_id: Identifier of the session being rendered.
        :param consume: When ``True`` the messages are removed from the
                        store as they are read; when ``False`` they are only
                        peeked at.
    """

    def __init__(self, manager: "FlashManager", session_id: str, consume: bool = True) -> None:
        """
            Construct the lazy list. Nothing is read from the store yet.

            :param manager: Manager whose store the messages are read from.
            :param session_id: Identifier of the session being rendered.
            :param consume: Remove the messages from the store when read.
        """
        super().__init__()
        self._manager = manager
        self._session_id = session_id
        self._consume = consume
        self._loaded = False
        self._lock = threading.Lock()
        return

    @property
    def loaded(self) -> bool:
        """
            Whether the messages have been read from the store.

            :returns: True once anything has looked at the messages.
        """
        return self._loaded

    def _load(self) -> None:
        """
            Read the messages from the store, the first time only.
        """
        with self._lock:
            if not self._loaded:
                if self._consume:
                    messages = self._manager.consume_all(self._session_id)
                else:
                    messages = self._manager.peek_all(self._session_id)
                super().extend(messages)
                self._loaded = True
        return

    def get_messages(self) -> List[FlashMessage]:
        """
            The pending messages as a plain list, read from the store on
            the first use and remembered afterwards.

            :returns: List of ``(category, message)`` tuples in insertion
                      order.
        """
        self._load()
        rtnval = super().copy()
        return rtnval

    def __call__(self) -> List[FlashMessage]:
        return self.get_messages()

    def __getitem__(self, index: Any) -> Any:
        self._load()
        return super().__getitem__(index)

    def __len__(self) -> int:
        self._load()
        return super().__len__()

    def __iter__(self) -> Iterator[FlashMessage]:
        self._load()
        return super().__iter__()

    def __reversed__(self) -> Iterator[FlashMessage]:
        self._load()
        return super().__reversed__()

    def __contains__(self, item: object) -> bool:
        self._load()
        return super().__contains__(item)

    def __eq__(self, other: object) -> bool:
        self._load()
        if isinstance(other, LazyFlashMessages):
            other._load()
        return super().__eq__(other)

    def __ne__(self, other: object) -> bool:
        self._load()
        if isinstance(other, LazyFlashMessages):
            other._load()
        return super().__ne__(other)

    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        if not self._loaded:
            return "LazyFlashMessages(<not read>)"
        return "LazyFlashMessages({})".format(super().__repr__())

    def copy(self) -> List[FlashMessage]:
        return self.get_messages()

    def count(self, value: Any) -> int:
        self._load()
        return super().count(value)

    def index(self, value: Any, *args: Any) -> int:
        self._load()
        return super().index(value, *args)


def make_flash_context_processor(
    manager: FlashManager,
    session_id_key: str = "session_id",
    messages_key: str = "flash_messages",
    consume: bool = True
) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
        Build a context processor that injects pending flash messages
        into the template context.

        The returned callable expects the rendering context to include
        the session identifier under ``session_id_key``. When the key
        is present and non-empty, the processor returns, under
        ``messages_key``, a :class:`LazyFlashMessages` for that session:
        a sequence of ``(category, message)`` tuples that reads the store
        only when the template uses it. A render that never shows the
        messages therefore leaves them for the page that does. When
        ``consume`` is ``True`` (the default) the messages are removed from
        the store as they are read, so a subsequent render does not
        duplicate them.

        :param manager: Manager whose store the processor reads from.
        :param session_id_key: Key under which the caller stores the
                               session identifier in the rendering
                               context.
        :param messages_key: Key under which the processor exposes the
                             pending messages.
        :param consume: When ``True``, drain the store when the messages
                        are read. When ``False``, peek without removing
                        — useful for admin tools or test introspection.

        :returns: A callable suitable for registration with
                  :class:`ccai.webworks.templating.context.ContextProcessorRegistry`.
    """

    def processor(context: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(context, dict):
            return {}

        session_id = context.get(session_id_key)
        if session_id is None:
            return {}
        if not isinstance(session_id, str):
            return {}
        if len(session_id) == 0:
            return {}

        messages = LazyFlashMessages(manager, session_id, consume=consume)

        return {messages_key: messages}

    return processor
