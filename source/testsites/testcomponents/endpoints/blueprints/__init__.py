"""
    blueprints

    One RestBlueprint per mj-* component group. Each blueprint serves its
    group's index page and the interactive per-component test pages.

    Importing this package imports every group blueprint module, which
    triggers RestBlueprint.attach_at registration so the Router discovers
    the routes at application startup.
"""

from testcomponents.endpoints.blueprints import selectionblueprint  # noqa: F401
from testcomponents.endpoints.blueprints import textblueprint  # noqa: F401
from testcomponents.endpoints.blueprints import buttonsblueprint  # noqa: F401
from testcomponents.endpoints.blueprints import navigationblueprint  # noqa: F401
from testcomponents.endpoints.blueprints import layoutblueprint  # noqa: F401
from testcomponents.endpoints.blueprints import feedbackblueprint  # noqa: F401
from testcomponents.endpoints.blueprints import overlaysblueprint  # noqa: F401
from testcomponents.endpoints.blueprints import datablueprint  # noqa: F401
from testcomponents.endpoints.blueprints import mediablueprint  # noqa: F401
from testcomponents.endpoints.blueprints import productivityblueprint  # noqa: F401
from testcomponents.endpoints.blueprints import chartsblueprint  # noqa: F401
