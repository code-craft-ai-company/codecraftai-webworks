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
