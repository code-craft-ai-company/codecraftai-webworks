"""
.. module:: flash
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Flash-message store, manager, and templating context processor
        for one-shot user feedback messages.

.. moduleauthor:: Automation Mojo LLC

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
      :class:`automojo.webworks.templating.context.ContextProcessorRegistry`.

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

Concurrency
-----------

The in-memory store uses a per-session list and is intended for the
single-process common case. Multi-worker deployments must use a backend
that is consistent across workers (Redis, database, etc.). The
abstract :class:`FlashStore` interface is intentionally tiny so swapping
in a real backend is a small implementation exercise.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import threading

from typing import Any, Callable, Dict, List, Optional, Tuple


DEFAULT_FLASH_CATEGORY = "info"

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
    """

    def __init__(self) -> None:
        """
            Construct an empty in-memory store.
        """
        self._messages: Dict[str, List[FlashMessage]] = {}
        self._lock = threading.RLock()
        return

    def add(self, session_id: str, category: str, message: str) -> None:
        """
            Append a message for the given session.

            :param session_id: Identifier of the target session.
            :param category: Category string.
            :param message: Plain-text message body.
        """
        with self._lock:
            if session_id not in self._messages:
                self._messages[session_id] = []
            self._messages[session_id].append((category, message))
        return

    def consume_all(self, session_id: str) -> List[FlashMessage]:
        """
            Return and remove all pending messages for the given session.

            :param session_id: Identifier of the target session.

            :returns: List of ``(category, message)`` tuples in insertion
                      order.
        """
        with self._lock:
            pending = self._messages.pop(session_id, None)

        if pending is None:
            return []

        # Return a fresh list so callers cannot mutate internal state.
        rtnval = list(pending)
        return rtnval

    def peek_all(self, session_id: str) -> List[FlashMessage]:
        """
            Return all pending messages for the given session without
            removing them.

            :param session_id: Identifier of the target session.

            :returns: List of ``(category, message)`` tuples in insertion
                      order.
        """
        with self._lock:
            pending = self._messages.get(session_id)
            if pending is None:
                return []
            rtnval = list(pending)
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
        is present and non-empty, the processor reads pending messages
        for that session and returns them under ``messages_key`` as a
        list of ``(category, message)`` tuples. When ``consume`` is
        ``True`` (the default) the messages are removed from the store
        after reading so a subsequent render does not duplicate them.

        :param manager: Manager whose store the processor reads from.
        :param session_id_key: Key under which the caller stores the
                               session identifier in the rendering
                               context.
        :param messages_key: Key under which the processor exposes the
                             list of pending messages.
        :param consume: When ``True``, drain the store as part of
                        rendering. When ``False``, peek without removing
                        — useful for admin tools or test introspection.

        :returns: A callable suitable for registration with
                  :class:`automojo.webworks.templating.context.ContextProcessorRegistry`.
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

        if consume:
            messages = manager.consume_all(session_id)
        else:
            messages = manager.peek_all(session_id)

        return {messages_key: messages}

    return processor
