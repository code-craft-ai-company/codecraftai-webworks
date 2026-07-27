"""
    Clears the process-global web application state before this testsite's
    modules import their application.

    Each testsite under source/testsites establishes a webapp persona and
    registers its endpoints at module import scope, which is what a real
    application does. testbase collects every test module into one process,
    so without this the second testsite imported inherits the first one's
    persona and endpoint registry — reported as an EndpointConflictError
    naming a handler from a site this one does not own, or as the persona
    singleton already being set.

    The reset lives here rather than in the testsite apps so those keep
    looking like the applications they are meant to demonstrate.
"""

from ccai.webworks.webapplication import reset_webapp_persona

reset_webapp_persona()
