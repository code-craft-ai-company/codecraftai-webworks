"""
.. module:: descriptor
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Endpoint descriptor dataclass for routing and documentation.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ccai.webworks.endpoints.constraints import EndpointConstraints
from ccai.webworks.endpoints.doc import Doc


#: Attribute stamped on a handler by :meth:`Endpoint.attach_at`, holding the
#: list of :class:`EndpointDescriptor` objects declared for it. The decorator
#: only marks; an :class:`EndpointRegistry` reads these marks when an
#: application explicitly collects a module. A handler may carry more than
#: one descriptor when it is decorated more than once.
#:
#: Defined here rather than beside the decorator so that registry.py can
#: read it without importing endpoint.py, which imports registry.py.
ENDPOINT_DESCRIPTORS_ATTR = "__webworks_endpoint_descriptors__"


def mark_handler(handler: Any, descriptor: "EndpointDescriptor") -> None:
    """
        Record a descriptor on the handler that declared it.

        Declaring an endpoint and registering one are separate steps. This is
        the declaring half: it attaches the descriptor to the handler and has
        no other effect, so importing a module of handlers changes nothing
        outside that module. An :class:`EndpointRegistry` performs the
        registering half when an application collects the module.

        The existing marks are read out of ``handler.__dict__`` rather than
        with :func:`getattr` so a method defined on a subclass never appends
        to a list belonging to its base class.

        :param handler: The callable declaring the endpoint.
        :param descriptor: The descriptor to record on it.
    """
    marks = handler.__dict__.get(ENDPOINT_DESCRIPTORS_ATTR)
    if marks is None:
        marks = []
        setattr(handler, ENDPOINT_DESCRIPTORS_ATTR, marks)

    marks.append(descriptor)

    return


#: Attribute stamped on the *class* an endpoint was declared through -- the
#: ``cls`` in ``cls.attach_at(...)`` or ``cls.attach_child(...)``.
#:
#: A handler mark answers "what does this function serve?". This answers the
#: other question, "what does this blueprint serve?", which the handler mark
#: cannot: the usual way to write a blueprint attaches free functions, and a
#: free function is not reachable from the class it was attached to.
#:
#:     class ApiBlueprint(Blueprint):
#:         base_path = "/api"
#:
#:     @ApiBlueprint.attach_at(leaf="users")
#:     def list_users(): ...
#:
#: ``list_users`` is a module-level name. Walking ``ApiBlueprint``'s body for
#: marked members finds nothing, so ``ApiBlueprint.register()`` returned an
#: empty list. It used to work only because attaching wrote into a
#: process-global registry that ``register()`` then filtered by base path.
ENDPOINT_DECLARED_ATTR = "__webworks_declared_descriptors__"


def declare_on_class(owner: Any, descriptor: "EndpointDescriptor") -> None:
    """
        Record a descriptor on the class it was declared through.

        Stored in ``owner.__dict__`` and read back the same way, never with
        :func:`getattr`. That is deliberate and is the whole safety property
        of this attribute: ``attach_at`` is inherited from
        :class:`~ccai.webworks.endpoints.endpoint.Endpoint`, so every bare
        ``Endpoint.attach_at(...)`` in a process declares on the shared root
        class. If lookup walked the MRO, each blueprint would see that pile
        and this would be the process-global registry again under another
        name. A class is asked only what was declared through it.

        :param owner: The class ``attach_at``/``attach_child`` was called on.
        :param descriptor: The descriptor to record on it.
    """
    declared = owner.__dict__.get(ENDPOINT_DECLARED_ATTR)
    if declared is None:
        declared = []
        setattr(owner, ENDPOINT_DECLARED_ATTR, declared)

    declared.append(descriptor)

    return


@dataclass
class EndpointDescriptor:
    """
        Record containing handler reference plus merged metadata for
        routing and documentation generation.
        
        This dataclass captures all information about an endpoint that
        is needed for routing, documentation generation, and security
        auditing.
        
        :param handler: The callable handler function for the endpoint.
        :param module: The module name where the handler is defined.
        :param leaf: URL leaf segment (e.g., "status" -> /status).
        :param path: Full URL path (alternative to leaf).
        :param methods: List of HTTP methods supported by the endpoint.
        :param version: API version string.
        :param tags: Documentation tags for grouping endpoints.
        :param constraints: Normalized constraint objects (AccessPolicy, RateLimit).
        :param doc: Documentation metadata (summary, description).
        :param extras: Additional metadata namespaced by endpoint type.
        :param on_conflict: What a registry should do when this descriptor
                            collides with one already registered at the same
                            path and method -- "error" or "replace". Declared
                            at the decorator and carried here because the
                            decorator only marks; the decision has to survive
                            until a registry actually collects the handler.
    """

    handler: Callable
    module: str
    leaf: Optional[str] = None
    path: Optional[str] = None
    methods: List[str] = field(default_factory=lambda: ["GET"])
    version: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    constraints: EndpointConstraints = field(default_factory=EndpointConstraints)
    doc: Optional[Doc] = None
    extras: Dict[str, Any] = field(default_factory=dict)
    on_conflict: str = "error"
    
    def to_openapi_path(self) -> Dict[str, Any]:
        """
            Convert descriptor to OpenAPI path item.
            
            Generates an OpenAPI-compatible path item dictionary that can
            be used to build OpenAPI specifications.
            
            :returns: Dictionary representing an OpenAPI path item.
        """
        path_item = {}
        
        for method in self.methods:
            operation = self._build_operation(method.lower())
            path_item[method.lower()] = operation
        
        return path_item
    
    def _build_operation(self, method: str) -> Dict[str, Any]:
        """
            Build an OpenAPI operation object for a specific HTTP method.
            
            :param method: The HTTP method (lowercase).
            
            :returns: Dictionary representing an OpenAPI operation.
        """
        operation: Dict[str, Any] = {
            "operationId": self._generate_operation_id(method),
        }
        
        # Add documentation fields
        if self.doc is not None:
            if self.doc.summary is not None:
                operation["summary"] = self.doc.summary
            if self.doc.description is not None:
                operation["description"] = self.doc.description
            if self.doc.deprecated:
                operation["deprecated"] = True
            if self.doc.external_docs is not None:
                operation["externalDocs"] = {"url": self.doc.external_docs}
        
        # Add tags
        if self.tags:
            operation["tags"] = list(self.tags)
        
        # Add security requirements from constraints
        security = self._build_security_requirements()
        if security:
            operation["security"] = security
        
        # Add responses placeholder
        operation["responses"] = {
            "200": {"description": "Successful response"}
        }
        
        # Add REST-specific extras if present
        if "rest" in self.extras:
            rest_extras = self.extras["rest"]
            if "request_schema" in rest_extras:
                operation["requestBody"] = {
                    "content": {
                        "application/json": {
                            "schema": rest_extras["request_schema"]
                        }
                    }
                }
            if "response_schema" in rest_extras:
                operation["responses"]["200"]["content"] = {
                    "application/json": {
                        "schema": rest_extras["response_schema"]
                    }
                }
            if "error_map" in rest_extras:
                for status_code, schema in rest_extras["error_map"].items():
                    operation["responses"][str(status_code)] = {
                        "description": f"Error response {status_code}",
                        "content": {
                            "application/json": {
                                "schema": schema
                            }
                        }
                    }
        
        return operation
    
    def _generate_operation_id(self, method: str) -> str:
        """
            Generate a unique operation ID for the endpoint.
            
            :param method: The HTTP method (lowercase).
            
            :returns: A unique operation ID string.
        """
        handler_name = self.handler.__name__
        path_part = self.path or self.leaf or "root"
        # Clean path for operation ID
        path_part = path_part.replace("/", "_").replace("{", "").replace("}", "").strip("_")
        return f"{method}_{path_part}_{handler_name}"
    
    def _build_security_requirements(self) -> List[Dict[str, List[str]]]:
        """
            Build OpenAPI security requirements from constraints.
            
            :returns: List of security requirement objects.
        """
        security = []
        
        if self.constraints.access_policy is not None:
            policy = self.constraints.access_policy
            if policy.require_auth:
                # Add OAuth2 security with scopes
                scopes = policy.scopes or self.constraints.scopes or []
                if scopes:
                    security.append({"oauth2": list(scopes)})
                else:
                    security.append({"oauth2": []})
        
        return security
    
    def to_security_row(self) -> Dict[str, Any]:
        """
            Convert descriptor to security audit row.
            
            Generates a dictionary suitable for security auditing and
            generating security maps (CSV/Markdown tables).
            
            :returns: Dictionary with security-relevant endpoint information.
        """
        # Determine the path to display
        if self.path is not None:
            display_path = self.path
        elif self.leaf is not None:
            display_path = f"/{self.leaf}"
        else:
            display_path = "/"
        
        row: Dict[str, Any] = {
            "path": display_path,
            "methods": ",".join(self.methods),
            "handler": f"{self.module}.{self.handler.__name__}",
            "access_policy": self._format_access_policy(),
            "scopes": ",".join(self._get_all_scopes()),
            "roles": ",".join(self._get_all_roles()),
            "rate_limit": self._format_rate_limit(),
            "summary": self.doc.summary if self.doc else None,
        }
        
        return row
    
    def _format_access_policy(self) -> str:
        """
            Format access policy for display.
            
            :returns: String representation of access policy.
        """
        if self.constraints.access_policy is None:
            return "none"
        
        policy = self.constraints.access_policy
        parts = []
        
        if policy.require_auth:
            parts.append("auth_required")
        else:
            parts.append("public")
        
        if policy.roles:
            parts.append(f"roles:{','.join(policy.roles)}")
        
        if policy.scopes:
            parts.append(f"scopes:{','.join(policy.scopes)}")
        
        return "|".join(parts) if parts else "none"
    
    def _get_all_scopes(self) -> List[str]:
        """
            Get all scopes from constraints and access policy.
            
            :returns: Combined list of scopes.
        """
        scopes = set(self.constraints.scopes)
        
        if self.constraints.access_policy is not None:
            scopes.update(self.constraints.access_policy.scopes)
        
        return sorted(scopes)
    
    def _get_all_roles(self) -> List[str]:
        """
            Get all roles from constraints and access policy.
            
            :returns: Combined list of roles.
        """
        roles = set(self.constraints.roles)
        
        if self.constraints.access_policy is not None:
            roles.update(self.constraints.access_policy.roles)
        
        return sorted(roles)
    
    def _format_rate_limit(self) -> str:
        """
            Format rate limit for display.
            
            :returns: String representation of rate limit.
        """
        if self.constraints.rate_limit is None:
            return "none"
        
        limit = self.constraints.rate_limit
        return f"{limit.requests}/{limit.window}s"
