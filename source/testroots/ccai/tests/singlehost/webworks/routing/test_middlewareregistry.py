"""
    Unit tests for the MiddlewareRegistry.

    These tests cover how the registry composes the effective pipeline of
    a request from its scopes.
"""

from ccai.webworks.routing.middlewareregistry import MiddlewareRegistry


def _make_middleware(label):
    """
        Create a pass-through middleware named by ``label``.
    """
    def middleware(request, call_next):
        return call_next(request)
    middleware.name = label
    return middleware


def test_compose_pipeline_orders_scopes_global_blueprint_route():
    """
        Global middleware comes first, then blueprint, then route middleware,
        whatever their priorities.
    """
    registry = MiddlewareRegistry()
    registry.register(_make_middleware("auth"), name="auth", scope="global", priority=50)
    registry.register(_make_middleware("bp"), name="bp", scope="blueprint", scope_key="shop", priority=10)
    registry.register(_make_middleware("rt"), name="rt", scope="route", scope_key="/shop/items", priority=5)

    pipeline = registry.compose_pipeline(blueprint_name="shop", route_path="/shop/items")

    assert pipeline.get_names() == ["auth", "bp", "rt"], f"Unexpected order {pipeline.get_names()}"
    return


def test_compose_pipeline_keeps_before_placement_within_a_scope():
    """
        A middleware registered before:auth stays before auth in the
        composed pipeline even when auth has a lower priority number.
    """
    registry = MiddlewareRegistry()
    registry.register(_make_middleware("auth"), name="auth", scope="global", priority=10)
    registry.register(_make_middleware("trace"), name="trace", scope="global", priority=50, position="before:auth")

    pipeline = registry.compose_pipeline()

    assert pipeline.get_names() == ["trace", "auth"], f"Unexpected order {pipeline.get_names()}"
    return


def test_export_effective_pipeline_matches_scope_order():
    """
        The exported pipeline lists the names in the composed order.
    """
    registry = MiddlewareRegistry()
    registry.register(_make_middleware("g"), name="g", scope="global", priority=90)
    registry.register(_make_middleware("r"), name="r", scope="route", scope_key="/x", priority=1)

    names = registry.export_effective_pipeline(route_path="/x")

    assert names == ["g", "r"], f"Unexpected order {names}"
    return
