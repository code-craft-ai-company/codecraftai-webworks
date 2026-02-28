"""
    Tests for the extensibility core data structures and enums.

    This module contains unit tests for ExtensionState, HookPriority,
    HookRegistration, ExtensionPointDefinition, LifecycleEvent,
    and ExtensionErrorInfo.
"""

from datetime import datetime

from automojo.webworks.extensibility.datastructures import (
    ExtensionErrorInfo,
    ExtensionPointDefinition,
    ExtensionState,
    HookPriority,
    HookRegistration,
    LifecycleEvent,
)


# =============================================================================
# Unit Tests for ExtensionState Enum
# =============================================================================

def test_extension_state_has_unknown_value():
    """
        Test that ExtensionState has an UNKNOWN member with value 'unknown'.
    """
    state = ExtensionState.UNKNOWN

    if state.value != "unknown":
        errmsg = f"Expected UNKNOWN value 'unknown', got '{state.value}'"
        raise AssertionError(errmsg)

    return


def test_extension_state_has_registered_value():
    """
        Test that ExtensionState has a REGISTERED member with value 'registered'.
    """
    state = ExtensionState.REGISTERED

    if state.value != "registered":
        errmsg = f"Expected REGISTERED value 'registered', got '{state.value}'"
        raise AssertionError(errmsg)

    return


def test_extension_state_has_initialized_value():
    """
        Test that ExtensionState has an INITIALIZED member with value 'initialized'.
    """
    state = ExtensionState.INITIALIZED

    if state.value != "initialized":
        errmsg = f"Expected INITIALIZED value 'initialized', got '{state.value}'"
        raise AssertionError(errmsg)

    return


def test_extension_state_has_active_value():
    """
        Test that ExtensionState has an ACTIVE member with value 'active'.
    """
    state = ExtensionState.ACTIVE

    if state.value != "active":
        errmsg = f"Expected ACTIVE value 'active', got '{state.value}'"
        raise AssertionError(errmsg)

    return


def test_extension_state_has_disabled_value():
    """
        Test that ExtensionState has a DISABLED member with value 'disabled'.
    """
    state = ExtensionState.DISABLED

    if state.value != "disabled":
        errmsg = f"Expected DISABLED value 'disabled', got '{state.value}'"
        raise AssertionError(errmsg)

    return


def test_extension_state_has_error_value():
    """
        Test that ExtensionState has an ERROR member with value 'error'.
    """
    state = ExtensionState.ERROR

    if state.value != "error":
        errmsg = f"Expected ERROR value 'error', got '{state.value}'"
        raise AssertionError(errmsg)

    return


def test_extension_state_has_quarantined_value():
    """
        Test that ExtensionState has a QUARANTINED member with value 'quarantined'.
    """
    state = ExtensionState.QUARANTINED

    if state.value != "quarantined":
        errmsg = f"Expected QUARANTINED value 'quarantined', got '{state.value}'"
        raise AssertionError(errmsg)

    return


def test_extension_state_has_seven_members():
    """
        Test that ExtensionState has exactly seven members.
    """
    member_count = len(ExtensionState)

    if member_count != 7:
        errmsg = f"Expected 7 ExtensionState members, got {member_count}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for HookPriority Constants
# =============================================================================

def test_hook_priority_highest_is_zero():
    """
        Test that HookPriority.HIGHEST is 0.
    """
    if HookPriority.HIGHEST != 0:
        errmsg = f"Expected HIGHEST to be 0, got {HookPriority.HIGHEST}"
        raise AssertionError(errmsg)

    return


def test_hook_priority_high_is_25():
    """
        Test that HookPriority.HIGH is 25.
    """
    if HookPriority.HIGH != 25:
        errmsg = f"Expected HIGH to be 25, got {HookPriority.HIGH}"
        raise AssertionError(errmsg)

    return


def test_hook_priority_normal_is_50():
    """
        Test that HookPriority.NORMAL is 50.
    """
    if HookPriority.NORMAL != 50:
        errmsg = f"Expected NORMAL to be 50, got {HookPriority.NORMAL}"
        raise AssertionError(errmsg)

    return


def test_hook_priority_low_is_75():
    """
        Test that HookPriority.LOW is 75.
    """
    if HookPriority.LOW != 75:
        errmsg = f"Expected LOW to be 75, got {HookPriority.LOW}"
        raise AssertionError(errmsg)

    return


def test_hook_priority_lowest_is_100():
    """
        Test that HookPriority.LOWEST is 100.
    """
    if HookPriority.LOWEST != 100:
        errmsg = f"Expected LOWEST to be 100, got {HookPriority.LOWEST}"
        raise AssertionError(errmsg)

    return


def test_hook_priority_ascending_order():
    """
        Test that priority constants are in ascending numeric order.
    """
    priorities = [
        HookPriority.HIGHEST,
        HookPriority.HIGH,
        HookPriority.NORMAL,
        HookPriority.LOW,
        HookPriority.LOWEST,
    ]

    for i in range(len(priorities) - 1):
        if priorities[i] >= priorities[i + 1]:
            errmsg = f"Priority at index {i} ({priorities[i]}) is not less than index {i + 1} ({priorities[i + 1]})"
            raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for HookRegistration Dataclass
# =============================================================================

def _sample_callback() -> None:
    """
        A sample callback function for testing HookRegistration.
    """
    return


def test_hook_registration_stores_callback():
    """
        Test that HookRegistration stores the callback reference.
    """
    reg = HookRegistration(
        callback=_sample_callback,
        priority=HookPriority.NORMAL,
        extension_name="test-ext"
    )

    if reg.callback is not _sample_callback:
        errmsg = "Expected callback to be the same function reference"
        raise AssertionError(errmsg)

    return


def test_hook_registration_stores_priority():
    """
        Test that HookRegistration stores the priority value.
    """
    reg = HookRegistration(
        callback=_sample_callback,
        priority=HookPriority.HIGH,
        extension_name="test-ext"
    )

    if reg.priority != HookPriority.HIGH:
        errmsg = f"Expected priority {HookPriority.HIGH}, got {reg.priority}"
        raise AssertionError(errmsg)

    return


def test_hook_registration_stores_extension_name():
    """
        Test that HookRegistration stores the extension name.
    """
    reg = HookRegistration(
        callback=_sample_callback,
        priority=HookPriority.NORMAL,
        extension_name="my-extension"
    )

    if reg.extension_name != "my-extension":
        errmsg = f"Expected extension_name 'my-extension', got '{reg.extension_name}'"
        raise AssertionError(errmsg)

    return


def test_hook_registration_default_before_is_empty():
    """
        Test that HookRegistration defaults before to an empty list.
    """
    reg = HookRegistration(
        callback=_sample_callback,
        priority=HookPriority.NORMAL,
        extension_name="test-ext"
    )

    if len(reg.before) != 0:
        errmsg = f"Expected empty before list, got {reg.before}"
        raise AssertionError(errmsg)

    return


def test_hook_registration_default_after_is_empty():
    """
        Test that HookRegistration defaults after to an empty list.
    """
    reg = HookRegistration(
        callback=_sample_callback,
        priority=HookPriority.NORMAL,
        extension_name="test-ext"
    )

    if len(reg.after) != 0:
        errmsg = f"Expected empty after list, got {reg.after}"
        raise AssertionError(errmsg)

    return


def test_hook_registration_with_before_and_after():
    """
        Test that HookRegistration stores before and after constraints.
    """
    reg = HookRegistration(
        callback=_sample_callback,
        priority=HookPriority.NORMAL,
        extension_name="test-ext",
        before=["ext-a"],
        after=["ext-b", "ext-c"]
    )

    if reg.before != ["ext-a"]:
        errmsg = f"Expected before ['ext-a'], got {reg.before}"
        raise AssertionError(errmsg)

    if reg.after != ["ext-b", "ext-c"]:
        errmsg = f"Expected after ['ext-b', 'ext-c'], got {reg.after}"
        raise AssertionError(errmsg)

    return


def test_hook_registration_allows_none_extension_name():
    """
        Test that HookRegistration allows None for extension_name.
    """
    reg = HookRegistration(
        callback=_sample_callback,
        priority=HookPriority.NORMAL,
        extension_name=None
    )

    if reg.extension_name is not None:
        errmsg = f"Expected extension_name None, got '{reg.extension_name}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ExtensionPointDefinition Dataclass
# =============================================================================

class _SampleInterface:
    """
        A sample interface class for testing ExtensionPointDefinition.
    """
    pass


def test_extension_point_definition_stores_name():
    """
        Test that ExtensionPointDefinition stores the name.
    """
    epd = ExtensionPointDefinition(
        name="my.extension.point",
        interface=_SampleInterface
    )

    if epd.name != "my.extension.point":
        errmsg = f"Expected name 'my.extension.point', got '{epd.name}'"
        raise AssertionError(errmsg)

    return


def test_extension_point_definition_stores_interface():
    """
        Test that ExtensionPointDefinition stores the interface type.
    """
    epd = ExtensionPointDefinition(
        name="my.point",
        interface=_SampleInterface
    )

    if epd.interface is not _SampleInterface:
        errmsg = "Expected interface to be _SampleInterface"
        raise AssertionError(errmsg)

    return


def test_extension_point_definition_default_description_is_empty():
    """
        Test that ExtensionPointDefinition defaults description to empty string.
    """
    epd = ExtensionPointDefinition(
        name="my.point",
        interface=_SampleInterface
    )

    if epd.description != "":
        errmsg = f"Expected empty description, got '{epd.description}'"
        raise AssertionError(errmsg)

    return


def test_extension_point_definition_default_multiple_is_true():
    """
        Test that ExtensionPointDefinition defaults multiple to True.
    """
    epd = ExtensionPointDefinition(
        name="my.point",
        interface=_SampleInterface
    )

    if epd.multiple is not True:
        errmsg = f"Expected multiple to be True, got {epd.multiple}"
        raise AssertionError(errmsg)

    return


def test_extension_point_definition_with_custom_values():
    """
        Test that ExtensionPointDefinition stores custom description and multiple.
    """
    epd = ExtensionPointDefinition(
        name="my.point",
        interface=_SampleInterface,
        description="A test extension point",
        multiple=False
    )

    if epd.description != "A test extension point":
        errmsg = f"Expected description 'A test extension point', got '{epd.description}'"
        raise AssertionError(errmsg)

    if epd.multiple is not False:
        errmsg = f"Expected multiple to be False, got {epd.multiple}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for LifecycleEvent Dataclass
# =============================================================================

def test_lifecycle_event_stores_event_type():
    """
        Test that LifecycleEvent stores the event type.
    """
    now = datetime.now()
    event = LifecycleEvent(
        event_type="activated",
        extension_name="test-ext",
        timestamp=now
    )

    if event.event_type != "activated":
        errmsg = f"Expected event_type 'activated', got '{event.event_type}'"
        raise AssertionError(errmsg)

    return


def test_lifecycle_event_stores_extension_name():
    """
        Test that LifecycleEvent stores the extension name.
    """
    now = datetime.now()
    event = LifecycleEvent(
        event_type="initialized",
        extension_name="my-ext",
        timestamp=now
    )

    if event.extension_name != "my-ext":
        errmsg = f"Expected extension_name 'my-ext', got '{event.extension_name}'"
        raise AssertionError(errmsg)

    return


def test_lifecycle_event_stores_timestamp():
    """
        Test that LifecycleEvent stores the timestamp.
    """
    now = datetime.now()
    event = LifecycleEvent(
        event_type="activated",
        extension_name="test-ext",
        timestamp=now
    )

    if event.timestamp is not now:
        errmsg = "Expected timestamp to be the same datetime instance"
        raise AssertionError(errmsg)

    return


def test_lifecycle_event_default_data_is_empty_dict():
    """
        Test that LifecycleEvent defaults data to an empty dict.
    """
    now = datetime.now()
    event = LifecycleEvent(
        event_type="activated",
        extension_name="test-ext",
        timestamp=now
    )

    if len(event.data) != 0:
        errmsg = f"Expected empty data dict, got {event.data}"
        raise AssertionError(errmsg)

    return


def test_lifecycle_event_with_custom_data():
    """
        Test that LifecycleEvent stores custom data.
    """
    now = datetime.now()
    event = LifecycleEvent(
        event_type="error",
        extension_name="test-ext",
        timestamp=now,
        data={"reason": "timeout"}
    )

    if event.data != {"reason": "timeout"}:
        errmsg = f"Expected data {{'reason': 'timeout'}}, got {event.data}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ExtensionErrorInfo Dataclass
# =============================================================================

def test_extension_error_info_stores_extension_name():
    """
        Test that ExtensionErrorInfo stores the extension name.
    """
    now = datetime.now()
    exc = RuntimeError("test error")
    info = ExtensionErrorInfo(
        extension_name="bad-ext",
        hook_name="before_request",
        exception=exc,
        timestamp=now,
        stack_trace="Traceback..."
    )

    if info.extension_name != "bad-ext":
        errmsg = f"Expected extension_name 'bad-ext', got '{info.extension_name}'"
        raise AssertionError(errmsg)

    return


def test_extension_error_info_stores_hook_name():
    """
        Test that ExtensionErrorInfo stores the hook name.
    """
    now = datetime.now()
    exc = RuntimeError("test error")
    info = ExtensionErrorInfo(
        extension_name="bad-ext",
        hook_name="on_app_init",
        exception=exc,
        timestamp=now,
        stack_trace="Traceback..."
    )

    if info.hook_name != "on_app_init":
        errmsg = f"Expected hook_name 'on_app_init', got '{info.hook_name}'"
        raise AssertionError(errmsg)

    return


def test_extension_error_info_allows_none_hook_name():
    """
        Test that ExtensionErrorInfo allows None for hook_name.
    """
    now = datetime.now()
    exc = RuntimeError("test error")
    info = ExtensionErrorInfo(
        extension_name="bad-ext",
        hook_name=None,
        exception=exc,
        timestamp=now,
        stack_trace="Traceback..."
    )

    if info.hook_name is not None:
        errmsg = f"Expected hook_name None, got '{info.hook_name}'"
        raise AssertionError(errmsg)

    return


def test_extension_error_info_stores_exception():
    """
        Test that ExtensionErrorInfo stores the exception reference.
    """
    now = datetime.now()
    exc = ValueError("bad value")
    info = ExtensionErrorInfo(
        extension_name="bad-ext",
        hook_name=None,
        exception=exc,
        timestamp=now,
        stack_trace="Traceback..."
    )

    if info.exception is not exc:
        errmsg = "Expected exception to be the same exception instance"
        raise AssertionError(errmsg)

    return


def test_extension_error_info_stores_stack_trace():
    """
        Test that ExtensionErrorInfo stores the stack trace string.
    """
    now = datetime.now()
    exc = RuntimeError("test error")
    trace = "Traceback (most recent call last):\n  File test.py"
    info = ExtensionErrorInfo(
        extension_name="bad-ext",
        hook_name=None,
        exception=exc,
        timestamp=now,
        stack_trace=trace
    )

    if info.stack_trace != trace:
        errmsg = f"Expected stack_trace to match, got '{info.stack_trace}'"
        raise AssertionError(errmsg)

    return
