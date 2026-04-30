"""
.. module:: accesspolicy
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Compatibility shim re-exporting the canonical
        :class:`automojo.webworks.security.accesspolicy.AccessPolicy`.

.. moduleauthor:: Automation Mojo LLC

This module historically defined a parallel ``AccessPolicy`` dataclass
distinct from the one in :mod:`automojo.webworks.security.accesspolicy`.
The two classes have been unified — see ``specs/features.md`` for the
rationale and the canonical surface — and the security-package version
is now the only implementation.

This module remains as a re-export so that existing imports from
``automojo.webworks.endpoints.accesspolicy`` continue to resolve. New
code should import :class:`AccessPolicy` directly from
:mod:`automojo.webworks.security.accesspolicy`.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from automojo.webworks.security.accesspolicy import AccessPolicy

__all__ = ["AccessPolicy"]
