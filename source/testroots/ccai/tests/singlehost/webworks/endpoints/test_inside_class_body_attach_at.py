"""
    Regression tests for the inside-class-body ``attach_at``
    decoration pattern.

    Background:
        Decorator expressions inside a class body run *before* the
        enclosing class is fully defined. A method like::

            class MyBP(RestBlueprint):
                base_path = "/inner"

                @RestBlueprint.attach_at(leaf="thing", methods=["GET"])
                def thing(self, request): ...

        invokes ``attach_at`` with ``cls = RestBlueprint`` (the
        parent) rather than ``cls = MyBP``, so the descriptor that
        lands in the registry would otherwise carry the *parent's*
        ``base_path`` (typically ``None``) and produce ``/thing``
        instead of the intended ``/inner/thing``.

        :meth:`Endpoint.__init_subclass__` repairs this by walking
        ``cls.__dict__``, finding handlers carrying the
        ``_endpoint_attach_at_metadata`` marker that ``attach_at``
        stamps, and re-resolving the registered descriptor's path
        against the actual subclass via
        :meth:`_compose_path_for_attach`.

    Covered:
        - ``RestBlueprint`` subclass with parent-class decoration:
          path is corrected to ``{subclass.base_path}/{leaf}``.
        - ``Blueprint`` subclass with parent-class decoration: same
          correction.
        - Outside-class-body decoration (the typical pattern,
          ``@MyBP.attach_at(...)`` at module scope) keeps working
          unchanged — no regression.
        - Stacked decorators on the same handler (multi-method) all
          have their paths corrected.
        - ``absolute=True`` paths are *not* re-prefixed by the
          subclass base.
        - Multi-level subclassing (``RestBlueprint -> A -> B``) where
          B redeclares the method picks up B's base path; A's
          base_path doesn't leak.
        - The marker is inert when the decorator was invoked on the
          subclass itself (no double-correction).
"""

from ccai.webworks.endpoints.blueprint import Blueprint
from ccai.webworks.endpoints.registry import EndpointRegistry
from ccai.webworks.endpoints.restblueprint import RestBlueprint


# =============================================================================
# RestBlueprint — the subclass that the original bug report targeted.
# =============================================================================


def test_rest_blueprint_inside_class_body_decoration_resolves_subclass_base_path():
    registry = EndpointRegistry()
    class InsideRestBP(RestBlueprint):
        base_path = "/inside-rest"

        @RestBlueprint.attach_at(leaf="thing", methods=["GET"])
        def thing(self, request):
            return {}

    registry.collect_from(InsideRestBP)
    descriptors = registry.collect()

    if len(descriptors) != 1:
        errmsg = "Expected exactly 1 descriptor, got {}".format(
            len(descriptors),
        )
        raise AssertionError(errmsg)

    if descriptors[0].path != "/inside-rest/thing":
        errmsg = (
            "Expected /inside-rest/thing, got {!r}".format(
                descriptors[0].path,
            )
        )
        raise AssertionError(errmsg)

    return


def test_rest_blueprint_outside_class_body_decoration_unchanged():
    # The typical pattern: decorate against the subclass after the
    # class is fully defined. No reliance on __init_subclass__; the
    # path should compose correctly at decoration time.
    registry = EndpointRegistry()
    class OutsideRestBP(RestBlueprint):
        base_path = "/outside-rest"

    @OutsideRestBP.attach_at(leaf="widget", methods=["GET"])
    def widget_handler(request):
        return {}

    registry.collect_from(widget_handler)
    descriptors = registry.collect()

    if len(descriptors) != 1:
        errmsg = "Expected exactly 1 descriptor, got {}".format(
            len(descriptors),
        )
        raise AssertionError(errmsg)

    if descriptors[0].path != "/outside-rest/widget":
        errmsg = (
            "Expected /outside-rest/widget, got {!r}".format(
                descriptors[0].path,
            )
        )
        raise AssertionError(errmsg)

    return


def test_rest_blueprint_inside_class_body_multi_method_stacking():
    registry = EndpointRegistry()
    class StackedRestBP(RestBlueprint):
        base_path = "/stacked"

        @RestBlueprint.attach_at(leaf="thing", methods=["GET"])
        @RestBlueprint.attach_at(leaf="thing", methods=["POST"])
        def thing(self, request):
            return {}

    registry.collect_from(StackedRestBP)
    descriptors = registry.collect()

    if len(descriptors) != 2:
        errmsg = (
            "Expected 2 descriptors (one per method), got {}".format(
                len(descriptors),
            )
        )
        raise AssertionError(errmsg)

    paths = sorted(d.path for d in descriptors)
    if paths != ["/stacked/thing", "/stacked/thing"]:
        errmsg = (
            "Expected both descriptors at /stacked/thing, got {!r}".format(
                paths,
            )
        )
        raise AssertionError(errmsg)

    methods = sorted(d.methods[0] for d in descriptors)
    if methods != ["GET", "POST"]:
        errmsg = "Expected GET + POST, got {!r}".format(methods)
        raise AssertionError(errmsg)

    return


def test_rest_blueprint_inside_class_body_absolute_path_not_reprefixed():
    registry = EndpointRegistry()
    class AbsoluteRestBP(RestBlueprint):
        base_path = "/abs"

        @RestBlueprint.attach_at(
            path="/totally/elsewhere",
            methods=["GET"],
            absolute=True,
        )
        def elsewhere(self, request):
            return {}

    registry.collect_from(AbsoluteRestBP)
    descriptors = registry.collect()

    if len(descriptors) != 1:
        errmsg = "Expected exactly 1 descriptor, got {}".format(
            len(descriptors),
        )
        raise AssertionError(errmsg)

    if descriptors[0].path != "/totally/elsewhere":
        errmsg = (
            "absolute=True path should not be re-prefixed with "
            "subclass base_path; got {!r}".format(descriptors[0].path)
        )
        raise AssertionError(errmsg)

    return


def test_rest_blueprint_inside_class_body_path_form():
    # User passes a ``path=`` instead of a ``leaf=``. The
    # re-resolution must produce the right composition.
    registry = EndpointRegistry()
    class PathFormBP(RestBlueprint):
        base_path = "/pathy"

        @RestBlueprint.attach_at(path="things/list", methods=["GET"])
        def list_things(self, request):
            return {}

    registry.collect_from(PathFormBP)
    descriptors = registry.collect()

    if len(descriptors) != 1:
        errmsg = "Expected exactly 1 descriptor, got {}".format(
            len(descriptors),
        )
        raise AssertionError(errmsg)

    if descriptors[0].path != "/pathy/things/list":
        errmsg = "Expected /pathy/things/list, got {!r}".format(
            descriptors[0].path,
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Blueprint (the non-REST variant) — same fix should apply.
# =============================================================================


def test_blueprint_inside_class_body_decoration_resolves_subclass_base_path():
    registry = EndpointRegistry()
    class InsideBP(Blueprint):
        base_path = "/inside-bp"

        @Blueprint.attach_at(leaf="thing", methods=["GET"])
        def thing(self, request):
            return {}

    registry.collect_from(InsideBP)
    descriptors = registry.collect()

    if len(descriptors) != 1:
        errmsg = "Expected exactly 1 descriptor, got {}".format(
            len(descriptors),
        )
        raise AssertionError(errmsg)

    if descriptors[0].path != "/inside-bp/thing":
        errmsg = "Expected /inside-bp/thing, got {!r}".format(
            descriptors[0].path,
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Multi-level subclassing.
# =============================================================================


def test_multi_level_subclass_picks_up_each_levels_base_path():
    registry = EndpointRegistry()
    class LevelOne(RestBlueprint):
        base_path = "/one"

        @RestBlueprint.attach_at(leaf="alpha", methods=["GET"])
        def alpha(self, request):
            return {}

    class LevelTwo(LevelOne):
        base_path = "/two"

        @RestBlueprint.attach_at(leaf="beta", methods=["GET"])
        def beta(self, request):
            return {}

    registry.collect_from(LevelOne, LevelTwo)
    descriptors = registry.collect()

    paths = sorted(d.path for d in descriptors)
    expected = sorted(["/one/alpha", "/two/beta"])

    if paths != expected:
        errmsg = "Expected {!r}, got {!r}".format(expected, paths)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Marker is inert when decoration was on the subclass itself.
# =============================================================================


def test_marker_does_not_re_resolve_when_decoration_is_on_subclass_itself():
    # Decorating against the *subclass* (which is a no-op for the
    # bug because ``cls`` is already the right class) should not
    # trigger any path correction in __init_subclass__.
    registry = EndpointRegistry()
    class SelfDecoratedBP(RestBlueprint):
        base_path = "/self"

    @SelfDecoratedBP.attach_at(leaf="thing", methods=["GET"])
    def self_thing(request):
        return {}

    registry.collect_from(self_thing)
    descriptors_after_first = registry.collect()

    if descriptors_after_first[0].path != "/self/thing":
        errmsg = (
            "Outside-body decoration on subclass should resolve "
            "directly; got {!r}".format(
                descriptors_after_first[0].path,
            )
        )
        raise AssertionError(errmsg)

    # Defining a deeper subclass with no method overrides should NOT
    # touch the existing descriptor (the walk only inspects the
    # subclass's own __dict__, not inherited methods).
    class DeeperBP(SelfDecoratedBP):
        base_path = "/deeper"

    descriptors_after_second = registry.collect()

    if descriptors_after_second[0].path != "/self/thing":
        errmsg = (
            "Defining DeeperBP must not re-prefix existing "
            "descriptor; got {!r}".format(
                descriptors_after_second[0].path,
            )
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Registry update_descriptor_path helper.
# =============================================================================


def test_registry_update_descriptor_path_moves_index_entries():
    registry = EndpointRegistry()
    class _BP(RestBlueprint):
        base_path = "/start"

    @_BP.attach_at(leaf="thing", methods=["GET", "POST"])
    def thing_handler(request):
        return {}

    registry.collect_from(thing_handler)
    descriptors = registry.collect()
    descriptor = descriptors[0]

    if descriptor.path != "/start/thing":
        errmsg = "Setup mismatch: expected /start/thing, got {!r}".format(
            descriptor.path,
        )
        raise AssertionError(errmsg)

    # Move the descriptor to a new path and confirm both index keys
    # follow it.
    registry.update_descriptor_path(
        descriptor=descriptor,
        new_path="/start/thing-renamed",
    )

    if descriptor.path != "/start/thing-renamed":
        errmsg = "Descriptor path not updated, got {!r}".format(
            descriptor.path,
        )
        raise AssertionError(errmsg)

    new_get = registry._path_method_index.get(
        ("/start/thing-renamed", "GET"),
    )
    new_post = registry._path_method_index.get(
        ("/start/thing-renamed", "POST"),
    )
    old_get = registry._path_method_index.get(
        ("/start/thing", "GET"),
    )

    if new_get is not descriptor:
        errmsg = "GET index key did not point at the descriptor"
        raise AssertionError(errmsg)
    if new_post is not descriptor:
        errmsg = "POST index key did not point at the descriptor"
        raise AssertionError(errmsg)
    if old_get is not None:
        errmsg = "Old GET index key was not removed"
        raise AssertionError(errmsg)

    return


def test_registry_update_descriptor_path_rejects_unregistered_descriptor():
    from ccai.webworks.endpoints.descriptor import EndpointDescriptor
    from ccai.webworks.endpoints.constraints import EndpointConstraints

    registry = EndpointRegistry()
    orphan = EndpointDescriptor(
        handler=lambda request: None,
        module="test",
        leaf=None,
        path="/orphan",
        methods=["GET"],
        version=None,
        tags=[],
        constraints=EndpointConstraints(),
        doc=None,
        extras={},
    )

    raised = False
    try:
        registry.update_descriptor_path(
            descriptor=orphan,
            new_path="/somewhere-else",
        )
    except ValueError:
        raised = True

    if not raised:
        errmsg = "Expected ValueError for unregistered descriptor"
        raise AssertionError(errmsg)

    return


def test_registry_update_descriptor_path_no_op_for_unchanged_path():
    registry = EndpointRegistry()
    class _BP(RestBlueprint):
        base_path = "/no-op"

    @_BP.attach_at(leaf="thing", methods=["GET"])
    def thing_handler(request):
        return {}

    registry.collect_from(thing_handler)
    descriptor = registry.collect()[0]

    registry.update_descriptor_path(
        descriptor=descriptor,
        new_path="/no-op/thing",  # same as current
    )

    # The index should still resolve correctly.
    indexed = registry._path_method_index.get(
        ("/no-op/thing", "GET"),
    )
    if indexed is not descriptor:
        errmsg = "No-op update broke the index"
        raise AssertionError(errmsg)

    return
