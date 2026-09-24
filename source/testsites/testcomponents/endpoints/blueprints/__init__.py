"""
    blueprints

    One RestBlueprint per mj-* component group. Each blueprint serves its
    group's index page and the interactive per-component test pages.

    Importing this package imports every group blueprint module, which
    declares (marks) each blueprint's routes. Declaring is not registering:
    the application claims the routes by passing :data:`BLUEPRINT_MODULES`
    to ``webapp.registry.collect_from`` in ``testcomponents/app.py``, the same
    way it collects the top-level ``handlers`` module.
    ``EndpointRegistry.collect_from`` walks a module one level and does not
    follow a package's submodules, so the package itself cannot be passed.
"""

from testcomponents.endpoints.blueprints import selectionblueprint
from testcomponents.endpoints.blueprints import textblueprint
from testcomponents.endpoints.blueprints import buttonsblueprint
from testcomponents.endpoints.blueprints import navigationblueprint
from testcomponents.endpoints.blueprints import layoutblueprint
from testcomponents.endpoints.blueprints import feedbackblueprint
from testcomponents.endpoints.blueprints import overlaysblueprint
from testcomponents.endpoints.blueprints import datablueprint
from testcomponents.endpoints.blueprints import mediablueprint
from testcomponents.endpoints.blueprints import productivityblueprint
from testcomponents.endpoints.blueprints import chartsblueprint


#: Every component group blueprint module, in the order the groups are
#: served. Pass these to ``EndpointRegistry.collect_from`` to register the
#: group index and per-component test page routes.
BLUEPRINT_MODULES = (
    selectionblueprint,
    textblueprint,
    buttonsblueprint,
    navigationblueprint,
    layoutblueprint,
    feedbackblueprint,
    overlaysblueprint,
    datablueprint,
    mediablueprint,
    productivityblueprint,
    chartsblueprint,
)
