"""
    Property-Based Tests for SSE Event Formatting (Property 8).

    Property 8: SSE Event Formatting
    For any SSE event with data, optional event name, optional id, and
    optional retry, formatting the event SHALL produce a string with proper
    field prefixes ("data:", "event:", "id:", "retry:") and double newline
    termination.

    Validates: Requirements 6.2, 6.3, 6.4, 6.5, 6.6
"""

import random
import string
from typing import Optional

from automojo.webworks.asgi.ssehandler import SSEEvent, SSEHandler


# =============================================================================
# Random Generators
# =============================================================================

def generate_data() -> str:
    """Generate random event data, possibly multi-line."""
    line_count = random.randint(1, 5)
    lines = []
    for _ in range(line_count):
        length = random.randint(1, 40)
        line = "".join(random.choices(string.ascii_letters + string.digits + " .,!?-", k=length))
        lines.append(line)
    return "\n".join(lines)


def generate_event_name() -> Optional[str]:
    """Generate an optional random event name."""
    if random.random() < 0.3:
        return None
    length = random.randint(1, 20)
    return "".join(random.choices(string.ascii_lowercase + string.digits + "-_", k=length))


def generate_event_id() -> Optional[str]:
    """Generate an optional random event ID."""
    if random.random() < 0.3:
        return None
    length = random.randint(1, 16)
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_retry() -> Optional[int]:
    """Generate an optional random retry interval in milliseconds."""
    if random.random() < 0.4:
        return None
    return random.randint(0, 30000)


def generate_sse_event() -> SSEEvent:
    """Generate a random SSEEvent with random fields."""
    return SSEEvent(
        data=generate_data(),
        event=generate_event_name(),
        id=generate_event_id(),
        retry=generate_retry(),
    )


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: asgi-layer, Property 8: SSE Event Formatting
# *For any* SSE event with data, optional event name, optional id, and
# optional retry, formatting the event SHALL produce a string with proper
# field prefixes ("data:", "event:", "id:", "retry:") and double newline
# termination.
# **Validates: Requirements 6.2, 6.3, 6.4, 6.5, 6.6**


def test_property_8_event_terminates_with_double_newline():
    """
        Property 8: Double Newline Termination

        For any SSE event, the formatted output SHALL end with a double
        newline (two consecutive newline characters), separating events
        per the SSE specification.

        **Validates: Requirement 6.3**
    """
    for iteration in range(100):
        event = generate_sse_event()
        formatted = event.format()

        if not formatted.endswith("\n\n"):
            errmsg = (
                f"Iteration {iteration}: formatted event does not end with "
                f"double newline. Got ending: {repr(formatted[-10:])}"
            )
            raise AssertionError(errmsg)

    return


def test_property_8_data_field_uses_proper_prefix():
    """
        Property 8: Data Field Prefix

        For any SSE event, every line of the data field SHALL be prefixed
        with "data: " in the formatted output.

        **Validates: Requirement 6.2**
    """
    for iteration in range(100):
        event = generate_sse_event()
        formatted = event.format()

        # Extract all data lines from the formatted output
        data_lines_in_output = [
            line for line in formatted.split("\n")
            if line.startswith("data: ") or line == "data: " or line.startswith("data:")
        ]

        # The original data split by newlines gives us expected data line count
        expected_data_lines = event.data.split("\n")

        if len(data_lines_in_output) != len(expected_data_lines):
            errmsg = (
                f"Iteration {iteration}: expected {len(expected_data_lines)} data lines, "
                f"got {len(data_lines_in_output)}. Data: {repr(event.data)}"
            )
            raise AssertionError(errmsg)

        # Each data line must use the "data: " prefix
        for i, line in enumerate(data_lines_in_output):
            if not line.startswith("data: "):
                errmsg = (
                    f"Iteration {iteration}: data line {i} does not start with "
                    f"'data: '. Got: {repr(line)}"
                )
                raise AssertionError(errmsg)

            # Verify the content after the prefix matches the original data line
            content = line[len("data: "):]
            if content != expected_data_lines[i]:
                errmsg = (
                    f"Iteration {iteration}: data line {i} content mismatch. "
                    f"Expected {repr(expected_data_lines[i])}, got {repr(content)}"
                )
                raise AssertionError(errmsg)

    return


def test_property_8_event_name_field_uses_proper_prefix():
    """
        Property 8: Event Name Field Prefix

        For any SSE event with an event name, the formatted output SHALL
        contain a line with the "event: " prefix followed by the event name.
        When no event name is provided, no "event:" line SHALL appear.

        **Validates: Requirement 6.4**
    """
    for iteration in range(100):
        event = generate_sse_event()
        formatted = event.format()
        lines = formatted.split("\n")

        event_lines = [line for line in lines if line.startswith("event:")]

        if event.event is not None:
            # Must have exactly one event line
            if len(event_lines) != 1:
                errmsg = (
                    f"Iteration {iteration}: expected 1 event line, "
                    f"got {len(event_lines)}. Event name: {repr(event.event)}"
                )
                raise AssertionError(errmsg)

            expected_line = f"event: {event.event}"
            if event_lines[0] != expected_line:
                errmsg = (
                    f"Iteration {iteration}: event line mismatch. "
                    f"Expected {repr(expected_line)}, got {repr(event_lines[0])}"
                )
                raise AssertionError(errmsg)
        else:
            # No event line should be present
            if len(event_lines) != 0:
                errmsg = (
                    f"Iteration {iteration}: expected no event lines when "
                    f"event is None, got {len(event_lines)}"
                )
                raise AssertionError(errmsg)

    return


def test_property_8_id_field_uses_proper_prefix():
    """
        Property 8: ID Field Prefix

        For any SSE event with an id, the formatted output SHALL contain
        a line with the "id: " prefix followed by the event ID. When no
        id is provided, no "id:" line SHALL appear.

        **Validates: Requirement 6.5**
    """
    for iteration in range(100):
        event = generate_sse_event()
        formatted = event.format()
        lines = formatted.split("\n")

        id_lines = [line for line in lines if line.startswith("id:")]

        if event.id is not None:
            if len(id_lines) != 1:
                errmsg = (
                    f"Iteration {iteration}: expected 1 id line, "
                    f"got {len(id_lines)}. ID: {repr(event.id)}"
                )
                raise AssertionError(errmsg)

            expected_line = f"id: {event.id}"
            if id_lines[0] != expected_line:
                errmsg = (
                    f"Iteration {iteration}: id line mismatch. "
                    f"Expected {repr(expected_line)}, got {repr(id_lines[0])}"
                )
                raise AssertionError(errmsg)
        else:
            if len(id_lines) != 0:
                errmsg = (
                    f"Iteration {iteration}: expected no id lines when "
                    f"id is None, got {len(id_lines)}"
                )
                raise AssertionError(errmsg)

    return


def test_property_8_retry_field_uses_proper_prefix():
    """
        Property 8: Retry Field Prefix

        For any SSE event with a retry interval, the formatted output SHALL
        contain a line with the "retry: " prefix followed by the retry value.
        When no retry is provided, no "retry:" line SHALL appear.

        **Validates: Requirement 6.6**
    """
    for iteration in range(100):
        event = generate_sse_event()
        formatted = event.format()
        lines = formatted.split("\n")

        retry_lines = [line for line in lines if line.startswith("retry:")]

        if event.retry is not None:
            if len(retry_lines) != 1:
                errmsg = (
                    f"Iteration {iteration}: expected 1 retry line, "
                    f"got {len(retry_lines)}. Retry: {event.retry}"
                )
                raise AssertionError(errmsg)

            expected_line = f"retry: {event.retry}"
            if retry_lines[0] != expected_line:
                errmsg = (
                    f"Iteration {iteration}: retry line mismatch. "
                    f"Expected {repr(expected_line)}, got {repr(retry_lines[0])}"
                )
                raise AssertionError(errmsg)
        else:
            if len(retry_lines) != 0:
                errmsg = (
                    f"Iteration {iteration}: expected no retry lines when "
                    f"retry is None, got {len(retry_lines)}"
                )
                raise AssertionError(errmsg)

    return


def test_property_8_field_ordering_in_formatted_output():
    """
        Property 8: Field Ordering

        For any SSE event, the formatted output SHALL place optional fields
        (event, id, retry) before the data lines, and the data lines SHALL
        appear last before the double newline termination.

        **Validates: Requirements 6.2, 6.3, 6.4, 6.5, 6.6**
    """
    for iteration in range(100):
        event = generate_sse_event()
        formatted = event.format()

        # Strip trailing newlines and split into content lines
        content = formatted.rstrip("\n")
        lines = content.split("\n")

        # Find the index of the first data line
        first_data_index = None
        for i, line in enumerate(lines):
            if line.startswith("data:"):
                first_data_index = i
                break

        if first_data_index is None:
            errmsg = (
                f"Iteration {iteration}: no data lines found in formatted output. "
                f"Data: {repr(event.data)}"
            )
            raise AssertionError(errmsg)

        # All lines after the first data line must also be data lines
        for i in range(first_data_index, len(lines)):
            if not lines[i].startswith("data:"):
                errmsg = (
                    f"Iteration {iteration}: non-data line found after first data line "
                    f"at index {i}. Line: {repr(lines[i])}"
                )
                raise AssertionError(errmsg)

        # All lines before the first data line must be optional field lines
        for i in range(first_data_index):
            line = lines[i]
            is_field = (
                line.startswith("event:") or
                line.startswith("id:") or
                line.startswith("retry:")
            )
            if not is_field:
                errmsg = (
                    f"Iteration {iteration}: unexpected line before data at index {i}. "
                    f"Line: {repr(line)}"
                )
                raise AssertionError(errmsg)

    return


def test_property_8_format_event_bytes_matches_format_string():
    """
        Property 8: SSEHandler.format_event Consistency

        For any SSE event, SSEHandler.format_event() SHALL return the
        UTF-8 encoded bytes of SSEEvent.format(), ensuring consistency
        between the string and bytes formatting paths.

        **Validates: Requirements 6.2, 6.3, 6.4, 6.5, 6.6**
    """
    handler = SSEHandler()

    for iteration in range(100):
        event = generate_sse_event()

        formatted_str = event.format()
        formatted_bytes = handler.format_event(event)

        expected_bytes = formatted_str.encode("utf-8")
        if formatted_bytes != expected_bytes:
            errmsg = (
                f"Iteration {iteration}: format_event bytes do not match "
                f"format() string encoded to UTF-8. "
                f"Expected {repr(expected_bytes[:80])}, got {repr(formatted_bytes[:80])}"
            )
            raise AssertionError(errmsg)

    return


def test_property_8_format_event_fields_matches_sse_event():
    """
        Property 8: format_event_fields Consistency

        For any combination of data, event, id, and retry values,
        SSEHandler.format_event_fields() SHALL produce the same output
        as constructing an SSEEvent and calling format_event().

        **Validates: Requirements 6.2, 6.3, 6.4, 6.5, 6.6**
    """
    handler = SSEHandler()

    for iteration in range(100):
        data = generate_data()
        event_name = generate_event_name()
        event_id = generate_event_id()
        retry = generate_retry()

        # Via format_event_fields
        result_fields = handler.format_event_fields(
            data=data,
            event=event_name,
            id=event_id,
            retry=retry,
        )

        # Via SSEEvent + format_event
        sse_event = SSEEvent(data=data, event=event_name, id=event_id, retry=retry)
        result_event = handler.format_event(sse_event)

        if result_fields != result_event:
            errmsg = (
                f"Iteration {iteration}: format_event_fields output differs from "
                f"SSEEvent.format_event output. "
                f"Fields: {repr(result_fields[:80])}, Event: {repr(result_event[:80])}"
            )
            raise AssertionError(errmsg)

    return


def test_property_8_multiline_data_each_line_prefixed():
    """
        Property 8: Multi-line Data Handling

        For any SSE event with multi-line data, each line of the data
        SHALL get its own "data: " prefix in the formatted output.

        **Validates: Requirement 6.2**
    """
    for iteration in range(100):
        # Generate data with guaranteed multiple lines
        line_count = random.randint(2, 8)
        data_lines = []
        for _ in range(line_count):
            length = random.randint(0, 30)
            line = "".join(random.choices(string.ascii_letters + string.digits + " ", k=length))
            data_lines.append(line)

        data = "\n".join(data_lines)
        event = SSEEvent(data=data)
        formatted = event.format()

        # Count data: lines in output
        output_data_lines = [
            line for line in formatted.split("\n")
            if line.startswith("data: ")
        ]

        if len(output_data_lines) != line_count:
            errmsg = (
                f"Iteration {iteration}: expected {line_count} data lines for "
                f"{line_count}-line data, got {len(output_data_lines)}"
            )
            raise AssertionError(errmsg)

        # Verify each data line content
        for i, output_line in enumerate(output_data_lines):
            content = output_line[len("data: "):]
            if content != data_lines[i]:
                errmsg = (
                    f"Iteration {iteration}: data line {i} content mismatch. "
                    f"Expected {repr(data_lines[i])}, got {repr(content)}"
                )
                raise AssertionError(errmsg)

    return
