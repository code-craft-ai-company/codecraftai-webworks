"""
    Property-Based Tests for Resource Limit Enforcement (Property 8).

    Property 8: Resource Limit Enforcement
    For any request body exceeding the configured limit, the server SHALL
    return HTTP 413 without processing the request body, and for any worker
    exceeding memory limits, the WorkerManager SHALL restart that worker.

    Validates: Requirements 11.2, 11.3, 11.4
"""

import random

from ccai.webworks.prodserver.resourcelimiter import (
    HeaderFieldTooLargeError,
    RequestBodyTooLargeError,
    ResourceLimiter,
)
from ccai.webworks.prodserver.serverconfig import ServerConfig


# =============================================================================
# Random Generators
# =============================================================================

def generate_body_size(limit: int) -> int:
    """
        Generate a random body size that exceeds the given limit.

        :param limit: The configured body size limit.

        :returns: A body size greater than the limit.
    """
    return limit + random.randint(1, limit * 2 + 1)


def generate_body_size_within(limit: int) -> int:
    """
        Generate a random body size within the given limit.

        :param limit: The configured body size limit.

        :returns: A body size less than or equal to the limit.
    """
    return random.randint(0, limit)


def generate_memory_limit() -> int:
    """
        Generate a random memory limit between 1MB and 1GB.
    """
    return random.randint(1024 * 1024, 1024 * 1024 * 1024)


def generate_request_body_limit() -> int:
    """
        Generate a random request body limit between 1KB and 10MB.
    """
    return random.randint(1024, 10 * 1024 * 1024)


def generate_field_size_limit() -> int:
    """
        Generate a random header field size limit between 100 and 16KB.
    """
    return random.randint(100, 16 * 1024)


def generate_worker_count() -> int:
    """
        Generate a random number of workers between 1 and 8.
    """
    return random.randint(1, 8)


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: production-server, Property 8: Resource Limit Enforcement
# *For any* request body exceeding the configured limit, the server SHALL
# return HTTP 413 without processing the request body, and for any worker
# exceeding memory limits, the WorkerManager SHALL restart that worker.
# **Validates: Requirements 11.2, 11.3, 11.4**


def test_property_8_memory_limit_detection():
    """
        Property 8: Memory Limit Detection

        For any worker whose memory usage exceeds the configured limit,
        check_worker_memory SHALL return True, indicating the worker
        should be restarted.

        **Validates: Requirement 11.2**
    """
    for iteration in range(50):
        memory_limit = generate_memory_limit()
        config = ServerConfig(limit_memory=memory_limit)
        limiter = ResourceLimiter(config=config)

        num_workers = generate_worker_count()

        for worker_id in range(num_workers):
            # Generate memory that exceeds the limit
            memory = memory_limit + random.randint(1, memory_limit)
            limiter.update_worker_memory(worker_id=worker_id, memory_bytes=memory)

            result = limiter.check_worker_memory(worker_id=worker_id)
            if result is not True:
                errmsg = (
                    f"Iteration {iteration}: worker {worker_id} with memory "
                    f"{memory} exceeding limit {memory_limit} should be "
                    f"flagged for restart"
                )
                raise AssertionError(errmsg)

    return


def test_property_8_memory_within_limit_not_flagged():
    """
        Property 8: Memory Within Limit Not Flagged

        For any worker whose memory usage is within the configured limit,
        check_worker_memory SHALL return False.

        **Validates: Requirement 11.2**
    """
    for iteration in range(50):
        memory_limit = generate_memory_limit()
        config = ServerConfig(limit_memory=memory_limit)
        limiter = ResourceLimiter(config=config)

        num_workers = generate_worker_count()

        for worker_id in range(num_workers):
            # Generate memory within the limit
            memory = random.randint(0, memory_limit)
            limiter.update_worker_memory(worker_id=worker_id, memory_bytes=memory)

            result = limiter.check_worker_memory(worker_id=worker_id)
            if result is not False:
                errmsg = (
                    f"Iteration {iteration}: worker {worker_id} with memory "
                    f"{memory} within limit {memory_limit} should not be "
                    f"flagged for restart"
                )
                raise AssertionError(errmsg)

    return


def test_property_8_request_body_exceeding_limit_returns_413():
    """
        Property 8: Request Body Exceeding Limit Returns 413

        For any request body size exceeding the configured limit,
        validate_request_body SHALL raise RequestBodyTooLargeError
        with status_code 413.

        **Validates: Requirements 11.3, 11.4**
    """
    for iteration in range(50):
        body_limit = generate_request_body_limit()
        config = ServerConfig(limit_request_body=body_limit)
        limiter = ResourceLimiter(config=config)

        body_size = generate_body_size(body_limit)

        raised = False
        try:
            limiter.validate_request_body(body_size=body_size)
        except RequestBodyTooLargeError as exc:
            raised = True
            if exc.status_code != 413:
                errmsg = (
                    f"Iteration {iteration}: expected status_code 413, "
                    f"got {exc.status_code}"
                )
                raise AssertionError(errmsg)
            if exc.body_size != body_size:
                errmsg = (
                    f"Iteration {iteration}: expected body_size {body_size}, "
                    f"got {exc.body_size}"
                )
                raise AssertionError(errmsg)
            if exc.limit != body_limit:
                errmsg = (
                    f"Iteration {iteration}: expected limit {body_limit}, "
                    f"got {exc.limit}"
                )
                raise AssertionError(errmsg)

        if not raised:
            errmsg = (
                f"Iteration {iteration}: expected RequestBodyTooLargeError "
                f"for body_size {body_size} exceeding limit {body_limit}"
            )
            raise AssertionError(errmsg)

    return


def test_property_8_request_body_within_limit_passes():
    """
        Property 8: Request Body Within Limit Passes

        For any request body size within the configured limit,
        validate_request_body SHALL not raise any exception.

        **Validates: Requirements 11.3, 11.4**
    """
    for iteration in range(50):
        body_limit = generate_request_body_limit()
        config = ServerConfig(limit_request_body=body_limit)
        limiter = ResourceLimiter(config=config)

        body_size = generate_body_size_within(body_limit)

        try:
            limiter.validate_request_body(body_size=body_size)
        except RequestBodyTooLargeError:
            errmsg = (
                f"Iteration {iteration}: body_size {body_size} within "
                f"limit {body_limit} should not raise"
            )
            raise AssertionError(errmsg)

    return


def test_property_8_workers_exceeding_memory_all_detected():
    """
        Property 8: All Workers Exceeding Memory Are Detected

        For any set of workers, get_workers_exceeding_memory SHALL
        return exactly those workers whose memory exceeds the limit.

        **Validates: Requirement 11.2**
    """
    for iteration in range(50):
        memory_limit = generate_memory_limit()
        config = ServerConfig(limit_memory=memory_limit)
        limiter = ResourceLimiter(config=config)

        num_workers = generate_worker_count()
        expected_exceeding = set()

        for worker_id in range(num_workers):
            if random.random() < 0.5:
                # Exceeding
                memory = memory_limit + random.randint(1, memory_limit)
                expected_exceeding.add(worker_id)
            else:
                # Within limit
                memory = random.randint(0, memory_limit)

            limiter.update_worker_memory(worker_id=worker_id, memory_bytes=memory)

        actual_exceeding = set(limiter.get_workers_exceeding_memory())

        if actual_exceeding != expected_exceeding:
            errmsg = (
                f"Iteration {iteration}: expected exceeding workers "
                f"{expected_exceeding}, got {actual_exceeding}"
            )
            raise AssertionError(errmsg)

    return


def test_property_8_header_field_size_exceeding_limit_raises():
    """
        Property 8: Header Field Size Exceeding Limit Raises

        For any header field value exceeding the configured limit,
        validate_header_field_size SHALL raise HeaderFieldTooLargeError.

        **Validates: Requirement 11.5 (related)**
    """
    for iteration in range(50):
        field_limit = generate_field_size_limit()
        config = ServerConfig(limit_request_field_size=field_limit)
        limiter = ResourceLimiter(config=config)

        # Generate a field value that exceeds the limit
        excess = random.randint(1, field_limit)
        field_value = "x" * (field_limit + excess)

        raised = False
        try:
            limiter.validate_header_field_size(field_value=field_value)
        except HeaderFieldTooLargeError as exc:
            raised = True
            if exc.status_code != 431:
                errmsg = (
                    f"Iteration {iteration}: expected status_code 431, "
                    f"got {exc.status_code}"
                )
                raise AssertionError(errmsg)

        if not raised:
            errmsg = (
                f"Iteration {iteration}: expected HeaderFieldTooLargeError "
                f"for field size {len(field_value)} exceeding limit {field_limit}"
            )
            raise AssertionError(errmsg)

    return


def test_property_8_zero_body_limit_allows_any_size():
    """
        Property 8: Zero Body Limit Allows Any Size

        When limit_request_body is 0 (unlimited), validate_request_body
        SHALL not raise for any body size.

        **Validates: Requirements 11.3, 11.4**
    """
    config = ServerConfig(limit_request_body=0)
    limiter = ResourceLimiter(config=config)

    for iteration in range(50):
        body_size = random.randint(0, 100 * 1024 * 1024)

        try:
            limiter.validate_request_body(body_size=body_size)
        except RequestBodyTooLargeError:
            errmsg = (
                f"Iteration {iteration}: body_size {body_size} should be "
                f"allowed when limit is 0 (unlimited)"
            )
            raise AssertionError(errmsg)

    return
