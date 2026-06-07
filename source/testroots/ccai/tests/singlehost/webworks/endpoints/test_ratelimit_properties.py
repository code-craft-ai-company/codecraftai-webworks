"""
.. module:: test_ratelimit_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for RateLimit stacking behavior.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the RateLimit class,
validating Property 8: Rate Limit Stacking across many generated
inputs.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import random

from ccai.webworks.endpoints.ratelimit import RateLimit


# =============================================================================
# Helper Functions for Generating Random Test Data
# =============================================================================

def generate_random_rate_limit() -> RateLimit:
    """Generate a random RateLimit with positive requests and window."""
    requests = random.randint(1, 10000)
    window = random.randint(1, 3600)
    return RateLimit(requests=requests, window=window)


def requests_per_second(limit: RateLimit) -> float:
    """Calculate the requests-per-second ratio for a rate limit."""
    if limit.window == 0:
        return float('inf')
    return limit.requests / limit.window


# =============================================================================
# Property 8: Rate Limit Stacking
# Feature: endpoint-abstractions, Property 8: Rate Limit Stacking
# Validates: Requirements 7.8
# =============================================================================


def test_property_most_restrictive_selects_lowest_rate():
    """
        Property 8: Rate Limit Stacking

        *For any* set of rate limits, most_restrictive SHALL return the
        limit with the lowest requests-per-second ratio, ensuring the
        most restrictive window applies.

        **Feature: endpoint-abstractions, Property 8: Rate Limit Stacking**
        **Validates: Requirements 7.8**
    """
    for iteration in range(100):
        num_limits = random.randint(2, 5)
        limits = [generate_random_rate_limit() for _ in range(num_limits)]

        result = RateLimit.most_restrictive(*limits)

        if result is None:
            errmsg = (
                f"Iteration {iteration}: most_restrictive returned None "
                f"for non-empty limits. limits={limits}"
            )
            raise AssertionError(errmsg)

        result_rps = requests_per_second(result)

        for limit in limits:
            limit_rps = requests_per_second(limit)
            if limit_rps < result_rps:
                errmsg = (
                    f"Iteration {iteration}: most_restrictive did not select "
                    f"the lowest rate. result={result} (rps={result_rps}), "
                    f"but found more restrictive limit={limit} (rps={limit_rps})"
                )
                raise AssertionError(errmsg)

    return


def test_property_most_restrictive_with_none_values():
    """
        Property 8: Rate Limit Stacking - None Handling

        *For any* mix of RateLimit objects and None values,
        most_restrictive SHALL ignore None values and return the most
        restrictive among the non-None limits.

        **Feature: endpoint-abstractions, Property 8: Rate Limit Stacking**
        **Validates: Requirements 7.8**
    """
    for iteration in range(100):
        num_limits = random.randint(1, 4)
        valid_limits = [generate_random_rate_limit() for _ in range(num_limits)]
        num_nones = random.randint(1, 3)

        mixed = list(valid_limits) + [None] * num_nones
        random.shuffle(mixed)

        result = RateLimit.most_restrictive(*mixed)

        if result is None:
            errmsg = (
                f"Iteration {iteration}: most_restrictive returned None "
                f"when valid limits exist. mixed={mixed}"
            )
            raise AssertionError(errmsg)

        result_rps = requests_per_second(result)

        for limit in valid_limits:
            limit_rps = requests_per_second(limit)
            if limit_rps < result_rps:
                errmsg = (
                    f"Iteration {iteration}: most_restrictive did not select "
                    f"the lowest rate among valid limits. result={result} "
                    f"(rps={result_rps}), but found more restrictive "
                    f"limit={limit} (rps={limit_rps})"
                )
                raise AssertionError(errmsg)

    return


def test_property_most_restrictive_all_none_returns_none():
    """
        Property 8: Rate Limit Stacking - All None

        *For any* call to most_restrictive with only None values,
        the result SHALL be None.

        **Feature: endpoint-abstractions, Property 8: Rate Limit Stacking**
        **Validates: Requirements 7.8**
    """
    for iteration in range(100):
        num_nones = random.randint(1, 5)
        nones = [None] * num_nones

        result = RateLimit.most_restrictive(*nones)

        if result is not None:
            errmsg = (
                f"Iteration {iteration}: most_restrictive should return None "
                f"when all inputs are None. Got result={result}"
            )
            raise AssertionError(errmsg)

    return


def test_property_most_restrictive_single_limit_returns_itself():
    """
        Property 8: Rate Limit Stacking - Single Limit Identity

        *For any* single RateLimit, most_restrictive SHALL return that
        same limit.

        **Feature: endpoint-abstractions, Property 8: Rate Limit Stacking**
        **Validates: Requirements 7.8**
    """
    for iteration in range(100):
        limit = generate_random_rate_limit()

        result = RateLimit.most_restrictive(limit)

        if result is not limit:
            errmsg = (
                f"Iteration {iteration}: most_restrictive with a single limit "
                f"should return that limit. limit={limit}, result={result}"
            )
            raise AssertionError(errmsg)

    return


def test_property_most_restrictive_is_idempotent():
    """
        Property 8: Rate Limit Stacking - Idempotency

        *For any* rate limit, calling most_restrictive with the same
        limit repeated multiple times SHALL return a limit equivalent
        to the input.

        **Feature: endpoint-abstractions, Property 8: Rate Limit Stacking**
        **Validates: Requirements 7.8**
    """
    for iteration in range(100):
        limit = generate_random_rate_limit()
        num_copies = random.randint(2, 5)

        result = RateLimit.most_restrictive(*([limit] * num_copies))

        if result.requests != limit.requests or result.window != limit.window:
            errmsg = (
                f"Iteration {iteration}: most_restrictive with identical limits "
                f"should return an equivalent limit. limit={limit}, result={result}"
            )
            raise AssertionError(errmsg)

    return


def test_property_most_restrictive_result_no_more_permissive_than_any_input():
    """
        Property 8: Rate Limit Stacking - Never More Permissive

        *For any* set of rate limits, the result of most_restrictive
        SHALL have a requests-per-second ratio less than or equal to
        every input limit's ratio. This ensures stacking never produces
        a more permissive limit.

        **Feature: endpoint-abstractions, Property 8: Rate Limit Stacking**
        **Validates: Requirements 7.8**
    """
    for iteration in range(100):
        num_limits = random.randint(2, 6)
        limits = [generate_random_rate_limit() for _ in range(num_limits)]

        result = RateLimit.most_restrictive(*limits)
        result_rps = requests_per_second(result)

        for idx, limit in enumerate(limits):
            limit_rps = requests_per_second(limit)
            if result_rps > limit_rps + 1e-12:
                errmsg = (
                    f"Iteration {iteration}: most_restrictive result is more "
                    f"permissive than input[{idx}]. result={result} "
                    f"(rps={result_rps}), input={limit} (rps={limit_rps})"
                )
                raise AssertionError(errmsg)

    return


def test_property_stacking_parent_child_most_restrictive_wins():
    """
        Property 8: Rate Limit Stacking - Parent/Child Stacking

        *For any* parent and child rate limits, stacking via
        most_restrictive SHALL select the more restrictive of the two,
        ensuring the endpoint is never less restricted than either
        the parent or the child intended.

        **Feature: endpoint-abstractions, Property 8: Rate Limit Stacking**
        **Validates: Requirements 7.8**
    """
    for iteration in range(100):
        parent_limit = generate_random_rate_limit()
        child_limit = generate_random_rate_limit()

        stacked = RateLimit.most_restrictive(parent_limit, child_limit)

        parent_rps = requests_per_second(parent_limit)
        child_rps = requests_per_second(child_limit)
        stacked_rps = requests_per_second(stacked)

        expected_rps = min(parent_rps, child_rps)

        if abs(stacked_rps - expected_rps) > 1e-12:
            errmsg = (
                f"Iteration {iteration}: Stacked rate limit should match the "
                f"more restrictive input. parent={parent_limit} (rps={parent_rps}), "
                f"child={child_limit} (rps={child_rps}), "
                f"stacked={stacked} (rps={stacked_rps}), "
                f"expected_rps={expected_rps}"
            )
            raise AssertionError(errmsg)

    return
