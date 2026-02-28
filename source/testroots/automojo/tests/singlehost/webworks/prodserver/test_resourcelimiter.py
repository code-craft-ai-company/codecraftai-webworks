"""
    Tests for the production server ResourceLimiter class.

    This module contains unit tests for resource limit enforcement
    including memory limit checking, request body size validation,
    header field size validation, resource warnings, and worker
    temporary directory management.
"""

import os

from automojo.webworks.prodserver.resourcelimiter import (
    HeaderFieldTooLargeError,
    RequestBodyTooLargeError,
    ResourceLimiter,
    RESOURCE_WARNING_THRESHOLD,
)
from automojo.webworks.prodserver.serverconfig import ServerConfig


# =============================================================================
# Unit Tests for RequestBodyTooLargeError
# =============================================================================

def test_request_body_too_large_error_stores_body_size():
    """
        Test that RequestBodyTooLargeError stores the body size.
    """
    err = RequestBodyTooLargeError(body_size=2000, limit=1000)

    if err.body_size != 2000:
        errmsg = f"Expected body_size 2000, got {err.body_size}"
        raise AssertionError(errmsg)

    return


def test_request_body_too_large_error_stores_limit():
    """
        Test that RequestBodyTooLargeError stores the limit.
    """
    err = RequestBodyTooLargeError(body_size=2000, limit=1000)

    if err.limit != 1000:
        errmsg = f"Expected limit 1000, got {err.limit}"
        raise AssertionError(errmsg)

    return


def test_request_body_too_large_error_status_code():
    """
        Test that RequestBodyTooLargeError returns status code 413.
    """
    err = RequestBodyTooLargeError(body_size=2000, limit=1000)

    if err.status_code != 413:
        errmsg = f"Expected status_code 413, got {err.status_code}"
        raise AssertionError(errmsg)

    return


def test_request_body_too_large_error_message():
    """
        Test that RequestBodyTooLargeError has a descriptive message.
    """
    err = RequestBodyTooLargeError(body_size=2000, limit=1000)

    msg = str(err)
    if "2000" not in msg or "1000" not in msg:
        errmsg = f"Expected message to contain sizes, got '{msg}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for HeaderFieldTooLargeError
# =============================================================================

def test_header_field_too_large_error_stores_field_size():
    """
        Test that HeaderFieldTooLargeError stores the field size.
    """
    err = HeaderFieldTooLargeError(field_size=10000, limit=8190)

    if err.field_size != 10000:
        errmsg = f"Expected field_size 10000, got {err.field_size}"
        raise AssertionError(errmsg)

    return


def test_header_field_too_large_error_stores_limit():
    """
        Test that HeaderFieldTooLargeError stores the limit.
    """
    err = HeaderFieldTooLargeError(field_size=10000, limit=8190)

    if err.limit != 8190:
        errmsg = f"Expected limit 8190, got {err.limit}"
        raise AssertionError(errmsg)

    return


def test_header_field_too_large_error_status_code():
    """
        Test that HeaderFieldTooLargeError returns status code 431.
    """
    err = HeaderFieldTooLargeError(field_size=10000, limit=8190)

    if err.status_code != 431:
        errmsg = f"Expected status_code 431, got {err.status_code}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ResourceLimiter - Memory Limits
# =============================================================================

def test_memory_limit_property_returns_configured_value():
    """
        Test that memory_limit returns the configured limit_memory value.
    """
    config = ServerConfig(limit_memory=1024 * 1024 * 256)
    limiter = ResourceLimiter(config=config)

    if limiter.memory_limit != 1024 * 1024 * 256:
        errmsg = f"Expected memory_limit {1024 * 1024 * 256}, got {limiter.memory_limit}"
        raise AssertionError(errmsg)

    return


def test_memory_limit_property_returns_none_when_not_set():
    """
        Test that memory_limit returns None when not configured.
    """
    config = ServerConfig()
    limiter = ResourceLimiter(config=config)

    if limiter.memory_limit is not None:
        errmsg = f"Expected memory_limit None, got {limiter.memory_limit}"
        raise AssertionError(errmsg)

    return


def test_update_worker_memory_tracks_usage():
    """
        Test that update_worker_memory stores the memory value.
    """
    config = ServerConfig()
    limiter = ResourceLimiter(config=config)

    limiter.update_worker_memory(worker_id=1, memory_bytes=50000)

    actual = limiter.get_worker_memory(worker_id=1)
    if actual != 50000:
        errmsg = f"Expected worker memory 50000, got {actual}"
        raise AssertionError(errmsg)

    return


def test_get_worker_memory_returns_zero_for_unknown():
    """
        Test that get_worker_memory returns 0 for untracked workers.
    """
    config = ServerConfig()
    limiter = ResourceLimiter(config=config)

    actual = limiter.get_worker_memory(worker_id=99)
    if actual != 0:
        errmsg = f"Expected 0 for unknown worker, got {actual}"
        raise AssertionError(errmsg)

    return


def test_check_worker_memory_returns_false_when_no_limit():
    """
        Test that check_worker_memory returns False when no limit is set.
    """
    config = ServerConfig()
    limiter = ResourceLimiter(config=config)

    limiter.update_worker_memory(worker_id=1, memory_bytes=999999999)

    result = limiter.check_worker_memory(worker_id=1)
    if result is not False:
        errmsg = "Expected False when no memory limit is set"
        raise AssertionError(errmsg)

    return


def test_check_worker_memory_returns_false_when_within_limit():
    """
        Test that check_worker_memory returns False when within limit.
    """
    config = ServerConfig(limit_memory=1000)
    limiter = ResourceLimiter(config=config)

    limiter.update_worker_memory(worker_id=1, memory_bytes=500)

    result = limiter.check_worker_memory(worker_id=1)
    if result is not False:
        errmsg = "Expected False when within memory limit"
        raise AssertionError(errmsg)

    return


def test_check_worker_memory_returns_true_when_exceeded():
    """
        Test that check_worker_memory returns True when limit is exceeded.
    """
    config = ServerConfig(limit_memory=1000)
    limiter = ResourceLimiter(config=config)

    limiter.update_worker_memory(worker_id=1, memory_bytes=1500)

    result = limiter.check_worker_memory(worker_id=1)
    if result is not True:
        errmsg = "Expected True when memory limit is exceeded"
        raise AssertionError(errmsg)

    return


def test_check_worker_memory_at_exact_limit_returns_false():
    """
        Test that check_worker_memory returns False at exact limit.
    """
    config = ServerConfig(limit_memory=1000)
    limiter = ResourceLimiter(config=config)

    limiter.update_worker_memory(worker_id=1, memory_bytes=1000)

    result = limiter.check_worker_memory(worker_id=1)
    if result is not False:
        errmsg = "Expected False at exact memory limit"
        raise AssertionError(errmsg)

    return


def test_get_workers_exceeding_memory_returns_exceeding_ids():
    """
        Test that get_workers_exceeding_memory returns correct worker IDs.
    """
    config = ServerConfig(limit_memory=1000)
    limiter = ResourceLimiter(config=config)

    limiter.update_worker_memory(worker_id=1, memory_bytes=500)
    limiter.update_worker_memory(worker_id=2, memory_bytes=1500)
    limiter.update_worker_memory(worker_id=3, memory_bytes=2000)

    result = limiter.get_workers_exceeding_memory()

    if 1 in result:
        errmsg = "Worker 1 should not be in exceeding list"
        raise AssertionError(errmsg)

    if 2 not in result:
        errmsg = "Worker 2 should be in exceeding list"
        raise AssertionError(errmsg)

    if 3 not in result:
        errmsg = "Worker 3 should be in exceeding list"
        raise AssertionError(errmsg)

    return


def test_get_workers_exceeding_memory_returns_empty_when_no_limit():
    """
        Test that get_workers_exceeding_memory returns empty when no limit.
    """
    config = ServerConfig()
    limiter = ResourceLimiter(config=config)

    limiter.update_worker_memory(worker_id=1, memory_bytes=999999)

    result = limiter.get_workers_exceeding_memory()
    if len(result) != 0:
        errmsg = f"Expected empty list, got {result}"
        raise AssertionError(errmsg)

    return


def test_remove_worker_clears_memory_tracking():
    """
        Test that remove_worker removes the worker from tracking.
    """
    config = ServerConfig()
    limiter = ResourceLimiter(config=config)

    limiter.update_worker_memory(worker_id=1, memory_bytes=5000)
    limiter.remove_worker(worker_id=1)

    actual = limiter.get_worker_memory(worker_id=1)
    if actual != 0:
        errmsg = f"Expected 0 after removal, got {actual}"
        raise AssertionError(errmsg)

    return


def test_remove_nonexistent_worker_is_safe():
    """
        Test that removing a nonexistent worker does not raise.
    """
    config = ServerConfig()
    limiter = ResourceLimiter(config=config)

    limiter.remove_worker(worker_id=99)

    return


# =============================================================================
# Unit Tests for ResourceLimiter - Request Body Limits
# =============================================================================

def test_request_body_limit_property():
    """
        Test that request_body_limit returns the configured value.
    """
    config = ServerConfig(limit_request_body=1024 * 1024)
    limiter = ResourceLimiter(config=config)

    if limiter.request_body_limit != 1024 * 1024:
        errmsg = f"Expected {1024 * 1024}, got {limiter.request_body_limit}"
        raise AssertionError(errmsg)

    return


def test_validate_request_body_passes_within_limit():
    """
        Test that validate_request_body passes when within limit.
    """
    config = ServerConfig(limit_request_body=1000)
    limiter = ResourceLimiter(config=config)

    limiter.validate_request_body(body_size=500)

    return


def test_validate_request_body_raises_when_exceeded():
    """
        Test that validate_request_body raises when limit is exceeded.
    """
    config = ServerConfig(limit_request_body=1000)
    limiter = ResourceLimiter(config=config)

    raised = False
    try:
        limiter.validate_request_body(body_size=1500)
    except RequestBodyTooLargeError as exc:
        raised = True
        if exc.body_size != 1500:
            errmsg = f"Expected body_size 1500, got {exc.body_size}"
            raise AssertionError(errmsg)
        if exc.limit != 1000:
            errmsg = f"Expected limit 1000, got {exc.limit}"
            raise AssertionError(errmsg)
        if exc.status_code != 413:
            errmsg = f"Expected status_code 413, got {exc.status_code}"
            raise AssertionError(errmsg)

    if not raised:
        errmsg = "Expected RequestBodyTooLargeError to be raised"
        raise AssertionError(errmsg)

    return


def test_validate_request_body_allows_zero_limit():
    """
        Test that validate_request_body allows any size when limit is 0.
    """
    config = ServerConfig(limit_request_body=0)
    limiter = ResourceLimiter(config=config)

    limiter.validate_request_body(body_size=999999999)

    return


def test_validate_request_body_at_exact_limit():
    """
        Test that validate_request_body passes at exact limit.
    """
    config = ServerConfig(limit_request_body=1000)
    limiter = ResourceLimiter(config=config)

    limiter.validate_request_body(body_size=1000)

    return


def test_validate_request_body_at_one_over_limit():
    """
        Test that validate_request_body raises at one byte over limit.
    """
    config = ServerConfig(limit_request_body=1000)
    limiter = ResourceLimiter(config=config)

    raised = False
    try:
        limiter.validate_request_body(body_size=1001)
    except RequestBodyTooLargeError:
        raised = True

    if not raised:
        errmsg = "Expected RequestBodyTooLargeError at 1001 bytes"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ResourceLimiter - Header Field Size Limits
# =============================================================================

def test_request_field_size_limit_property():
    """
        Test that request_field_size_limit returns the configured value.
    """
    config = ServerConfig(limit_request_field_size=4096)
    limiter = ResourceLimiter(config=config)

    if limiter.request_field_size_limit != 4096:
        errmsg = f"Expected 4096, got {limiter.request_field_size_limit}"
        raise AssertionError(errmsg)

    return


def test_validate_header_field_size_passes_within_limit():
    """
        Test that validate_header_field_size passes when within limit.
    """
    config = ServerConfig(limit_request_field_size=100)
    limiter = ResourceLimiter(config=config)

    limiter.validate_header_field_size(field_value="short value")

    return


def test_validate_header_field_size_raises_when_exceeded():
    """
        Test that validate_header_field_size raises when limit is exceeded.
    """
    config = ServerConfig(limit_request_field_size=10)
    limiter = ResourceLimiter(config=config)

    raised = False
    try:
        limiter.validate_header_field_size(field_value="a" * 20)
    except HeaderFieldTooLargeError as exc:
        raised = True
        if exc.field_size != 20:
            errmsg = f"Expected field_size 20, got {exc.field_size}"
            raise AssertionError(errmsg)
        if exc.limit != 10:
            errmsg = f"Expected limit 10, got {exc.limit}"
            raise AssertionError(errmsg)
        if exc.status_code != 431:
            errmsg = f"Expected status_code 431, got {exc.status_code}"
            raise AssertionError(errmsg)

    if not raised:
        errmsg = "Expected HeaderFieldTooLargeError to be raised"
        raise AssertionError(errmsg)

    return


def test_validate_header_field_size_allows_zero_limit():
    """
        Test that validate_header_field_size allows any size when limit is 0.
    """
    config = ServerConfig(limit_request_field_size=0)
    limiter = ResourceLimiter(config=config)

    limiter.validate_header_field_size(field_value="x" * 100000)

    return


def test_validate_header_field_size_at_exact_limit():
    """
        Test that validate_header_field_size passes at exact limit.
    """
    config = ServerConfig(limit_request_field_size=10)
    limiter = ResourceLimiter(config=config)

    limiter.validate_header_field_size(field_value="a" * 10)

    return


# =============================================================================
# Unit Tests for ResourceLimiter - Resource Warnings
# =============================================================================

def test_check_resource_warnings_returns_empty_when_no_limit():
    """
        Test that check_resource_warnings returns empty when no limit.
    """
    config = ServerConfig()
    limiter = ResourceLimiter(config=config)

    limiter.update_worker_memory(worker_id=1, memory_bytes=999999)

    warnings = limiter.check_resource_warnings()
    if len(warnings) != 0:
        errmsg = f"Expected no warnings, got {warnings}"
        raise AssertionError(errmsg)

    return


def test_check_resource_warnings_warns_when_approaching_limit():
    """
        Test that check_resource_warnings warns when approaching limit.
    """
    config = ServerConfig(limit_memory=1000)
    limiter = ResourceLimiter(config=config)

    # 850 bytes is above 80% threshold (800) but below limit (1000)
    limiter.update_worker_memory(worker_id=1, memory_bytes=850)

    warnings = limiter.check_resource_warnings()
    if len(warnings) != 1:
        errmsg = f"Expected 1 warning, got {len(warnings)}"
        raise AssertionError(errmsg)

    return


def test_check_resource_warnings_no_warning_below_threshold():
    """
        Test that check_resource_warnings does not warn below threshold.
    """
    config = ServerConfig(limit_memory=1000)
    limiter = ResourceLimiter(config=config)

    # 500 bytes is below 80% threshold (800)
    limiter.update_worker_memory(worker_id=1, memory_bytes=500)

    warnings = limiter.check_resource_warnings()
    if len(warnings) != 0:
        errmsg = f"Expected no warnings, got {warnings}"
        raise AssertionError(errmsg)

    return


def test_check_resource_warnings_no_warning_when_exceeded():
    """
        Test that check_resource_warnings does not warn when already exceeded.
        Workers exceeding the limit should be restarted, not warned.
    """
    config = ServerConfig(limit_memory=1000)
    limiter = ResourceLimiter(config=config)

    # 1500 bytes exceeds the limit, should not generate a warning
    limiter.update_worker_memory(worker_id=1, memory_bytes=1500)

    warnings = limiter.check_resource_warnings()
    if len(warnings) != 0:
        errmsg = f"Expected no warnings for exceeded limit, got {warnings}"
        raise AssertionError(errmsg)

    return


def test_get_last_warnings_returns_previous_warnings():
    """
        Test that get_last_warnings returns warnings from last check.
    """
    config = ServerConfig(limit_memory=1000)
    limiter = ResourceLimiter(config=config)

    limiter.update_worker_memory(worker_id=1, memory_bytes=850)
    limiter.check_resource_warnings()

    last = limiter.get_last_warnings()
    if len(last) != 1:
        errmsg = f"Expected 1 last warning, got {len(last)}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ResourceLimiter - Worker Temp Directory
# =============================================================================

def test_setup_worker_tmp_dir_creates_directory():
    """
        Test that setup_worker_tmp_dir creates a temporary directory.
    """
    config = ServerConfig()
    limiter = ResourceLimiter(config=config)

    result = limiter.setup_worker_tmp_dir()

    if result is None:
        errmsg = "Expected a temp directory path, got None"
        raise AssertionError(errmsg)

    if not os.path.isdir(result):
        errmsg = f"Expected directory to exist at {result}"
        raise AssertionError(errmsg)

    # Clean up
    limiter.cleanup_worker_tmp_dir()

    return


def test_worker_tmp_dir_property():
    """
        Test that worker_tmp_dir property returns the path after setup.
    """
    config = ServerConfig()
    limiter = ResourceLimiter(config=config)

    if limiter.worker_tmp_dir is not None:
        errmsg = "Expected None before setup"
        raise AssertionError(errmsg)

    limiter.setup_worker_tmp_dir()

    if limiter.worker_tmp_dir is None:
        errmsg = "Expected path after setup"
        raise AssertionError(errmsg)

    # Clean up
    limiter.cleanup_worker_tmp_dir()

    return


def test_cleanup_worker_tmp_dir_removes_directory():
    """
        Test that cleanup_worker_tmp_dir removes the directory.
    """
    config = ServerConfig()
    limiter = ResourceLimiter(config=config)

    path = limiter.setup_worker_tmp_dir()
    limiter.cleanup_worker_tmp_dir()

    if limiter.worker_tmp_dir is not None:
        errmsg = "Expected None after cleanup"
        raise AssertionError(errmsg)

    return


def test_cleanup_worker_tmp_dir_safe_when_not_set():
    """
        Test that cleanup_worker_tmp_dir is safe when no dir is set.
    """
    config = ServerConfig()
    limiter = ResourceLimiter(config=config)

    limiter.cleanup_worker_tmp_dir()

    return


# =============================================================================
# Unit Tests for ResourceLimiter - Status and Reset
# =============================================================================

def test_get_status_returns_expected_fields():
    """
        Test that get_status returns all expected fields.
    """
    config = ServerConfig(limit_memory=1000, limit_request_body=5000)
    limiter = ResourceLimiter(config=config)

    limiter.update_worker_memory(worker_id=1, memory_bytes=500)

    status = limiter.get_status()

    expected_keys = {
        "memory_limit",
        "request_body_limit",
        "request_field_size_limit",
        "worker_memory",
        "worker_tmp_dir",
        "warnings",
    }
    actual_keys = set(status.keys())

    if actual_keys != expected_keys:
        errmsg = f"Expected keys {expected_keys}, got {actual_keys}"
        raise AssertionError(errmsg)

    if status["memory_limit"] != 1000:
        errmsg = f"Expected memory_limit 1000, got {status['memory_limit']}"
        raise AssertionError(errmsg)

    if status["request_body_limit"] != 5000:
        errmsg = f"Expected request_body_limit 5000, got {status['request_body_limit']}"
        raise AssertionError(errmsg)

    return


def test_reset_clears_all_state():
    """
        Test that reset clears all tracked state.
    """
    config = ServerConfig(limit_memory=1000)
    limiter = ResourceLimiter(config=config)

    limiter.update_worker_memory(worker_id=1, memory_bytes=850)
    limiter.check_resource_warnings()

    limiter.reset()

    if limiter.get_worker_memory(worker_id=1) != 0:
        errmsg = "Expected worker memory cleared after reset"
        raise AssertionError(errmsg)

    if len(limiter.get_last_warnings()) != 0:
        errmsg = "Expected warnings cleared after reset"
        raise AssertionError(errmsg)

    return
