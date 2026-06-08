"""
    Tests for the RateLimit dataclass.
    
    This module contains unit tests for the rate limiting constraint dataclass.
"""

from ccai.webworks.endpoints.ratelimit import RateLimit


# =============================================================================
# Unit Tests for RateLimit - Basic Construction
# =============================================================================

def test_ratelimit_construction():
    """
        Test that RateLimit can be constructed with requests and window.
    """
    limit = RateLimit(requests=100, window=60)
    
    if limit.requests != 100:
        errmsg = f"Expected requests 100, got {limit.requests}"
        raise AssertionError(errmsg)
    
    if limit.window != 60:
        errmsg = f"Expected window 60, got {limit.window}"
        raise AssertionError(errmsg)
    
    return


def test_ratelimit_is_dataclass():
    """
        Test that RateLimit is a proper dataclass with equality.
    """
    limit1 = RateLimit(requests=100, window=60)
    limit2 = RateLimit(requests=100, window=60)
    
    if limit1 != limit2:
        errmsg = "Expected equal RateLimit instances to be equal"
        raise AssertionError(errmsg)
    
    return


def test_ratelimit_inequality():
    """
        Test that different RateLimit instances are not equal.
    """
    limit1 = RateLimit(requests=100, window=60)
    limit2 = RateLimit(requests=50, window=60)
    
    if limit1 == limit2:
        errmsg = "Expected different RateLimit instances to not be equal"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for RateLimit - most_restrictive classmethod
# =============================================================================

def test_most_restrictive_returns_none_for_empty():
    """
        Test that most_restrictive returns None when no limits provided.
    """
    result = RateLimit.most_restrictive()
    
    if result is not None:
        errmsg = f"Expected None, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_most_restrictive_returns_none_for_all_none():
    """
        Test that most_restrictive returns None when all limits are None.
    """
    result = RateLimit.most_restrictive(None, None, None)
    
    if result is not None:
        errmsg = f"Expected None, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_most_restrictive_returns_single_limit():
    """
        Test that most_restrictive returns the single limit when only one provided.
    """
    limit = RateLimit(requests=100, window=60)
    result = RateLimit.most_restrictive(limit)
    
    if result is not limit:
        errmsg = f"Expected the same limit object, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_most_restrictive_ignores_none_values():
    """
        Test that most_restrictive ignores None values.
    """
    limit = RateLimit(requests=100, window=60)
    result = RateLimit.most_restrictive(None, limit, None)
    
    if result is not limit:
        errmsg = f"Expected the limit object, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_most_restrictive_selects_lower_rate():
    """
        Test that most_restrictive selects the limit with lower requests per second.
    """
    # 100 requests per 60 seconds = 1.67 req/s
    limit1 = RateLimit(requests=100, window=60)
    # 50 requests per 60 seconds = 0.83 req/s (more restrictive)
    limit2 = RateLimit(requests=50, window=60)
    
    result = RateLimit.most_restrictive(limit1, limit2)
    
    if result is not limit2:
        errmsg = f"Expected limit2 (more restrictive), got {result}"
        raise AssertionError(errmsg)
    
    return


def test_most_restrictive_considers_window():
    """
        Test that most_restrictive considers window when comparing.
    """
    # 100 requests per 60 seconds = 1.67 req/s
    limit1 = RateLimit(requests=100, window=60)
    # 100 requests per 120 seconds = 0.83 req/s (more restrictive)
    limit2 = RateLimit(requests=100, window=120)
    
    result = RateLimit.most_restrictive(limit1, limit2)
    
    if result is not limit2:
        errmsg = f"Expected limit2 (more restrictive), got {result}"
        raise AssertionError(errmsg)
    
    return


def test_most_restrictive_with_multiple_limits():
    """
        Test that most_restrictive works with multiple limits.
    """
    # 100 req/60s = 1.67 req/s
    limit1 = RateLimit(requests=100, window=60)
    # 50 req/60s = 0.83 req/s
    limit2 = RateLimit(requests=50, window=60)
    # 10 req/60s = 0.17 req/s (most restrictive)
    limit3 = RateLimit(requests=10, window=60)
    
    result = RateLimit.most_restrictive(limit1, limit2, limit3)
    
    if result is not limit3:
        errmsg = f"Expected limit3 (most restrictive), got {result}"
        raise AssertionError(errmsg)
    
    return


def test_most_restrictive_with_mixed_none_and_limits():
    """
        Test that most_restrictive works with mixed None and limit values.
    """
    limit1 = RateLimit(requests=100, window=60)
    limit2 = RateLimit(requests=50, window=60)
    
    result = RateLimit.most_restrictive(None, limit1, None, limit2, None)
    
    if result is not limit2:
        errmsg = f"Expected limit2 (more restrictive), got {result}"
        raise AssertionError(errmsg)
    
    return
