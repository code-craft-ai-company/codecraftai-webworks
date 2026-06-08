"""
.. module:: accesspolicy
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Compatibility shim re-exporting the canonical
        :class:`ccai.webworks.security.accesspolicy.AccessPolicy`.

.. moduleauthor:: Code Craft AI LLC

This module historically defined a parallel ``AccessPolicy`` dataclass
distinct from the one in :mod:`ccai.webworks.security.accesspolicy`.
The two classes have been unified — see ``specs/features.md`` for the
rationale and the canonical surface — and the security-package version
is now the only implementation.

This module remains as a re-export so that existing imports from
``ccai.webworks.endpoints.accesspolicy`` continue to resolve. New
code should import :class:`AccessPolicy` directly from
:mod:`ccai.webworks.security.accesspolicy`.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from ccai.webworks.security.accesspolicy import AccessPolicy

__all__ = ["AccessPolicy"]
