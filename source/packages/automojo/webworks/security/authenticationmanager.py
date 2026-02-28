"""
.. module:: authenticationmanager
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Authentication manager that coordinates multiple authentication
        providers to authenticate incoming requests.

.. moduleauthor:: Automation Mojo LLC

This module provides the Authentication_Manager class that manages multiple
authentication providers and coordinates the authentication process. Providers
are registered with priority ordering and tried in sequence until one succeeds
or all fail. When all providers fail, a guest Security_Context is returned.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from typing import Any, List

from automojo.webworks.security.authenticationprovider import Authentication_Provider
from automojo.webworks.security.securitycontext import Security_Context


class Authentication_Manager:
    """
        Manages multiple authentication providers and coordinates the
        authentication process.

        Providers are registered via register_provider() and sorted by
        priority (lower number = higher priority). When authenticate() is
        called, each provider is tried in priority order until one returns
        a Security_Context. If all providers return None, a guest context
        is returned.
    """

    def __init__(self):
        self._providers: List[Authentication_Provider] = []
        return

    @property
    def providers(self) -> List[Authentication_Provider]:
        """
            Return the list of registered providers in priority order.

            :returns: A list of Authentication_Provider instances.
        """
        rtnval = list(self._providers)
        return rtnval

    def register_provider(self, provider: Authentication_Provider) -> None:
        """
            Register an authentication provider.

            The provider is added to the internal list and the list is
            re-sorted by priority so that providers with lower priority
            numbers are tried first.

            :param provider: The authentication provider to register.
        """
        self._providers.append(provider)
        self._providers.sort(key=lambda p: p.priority)
        return

    def authenticate(self, request: Any) -> Security_Context:
        """
            Attempt authentication using all registered providers.

            Tries each provider in priority order until one succeeds.
            Returns a guest context if all providers fail or return None.

            :param request: The incoming request to authenticate.

            :returns: A Security_Context, either authenticated or guest.
        """
        providers = self._providers

        for provider in providers:
            result = provider.authenticate(request)
            if result is not None:
                return result

        rtnval = Security_Context.guest()
        return rtnval

    async def authenticate_async(self, request: Any) -> Security_Context:
        """
            Attempt authentication using all registered providers asynchronously.

            Tries each provider in priority order until one succeeds.
            Returns a guest context if all providers fail or return None.

            :param request: The incoming request to authenticate.

            :returns: A Security_Context, either authenticated or guest.
        """
        providers = self._providers

        for provider in providers:
            result = await provider.authenticate_async(request)
            if result is not None:
                return result

        rtnval = Security_Context.guest()
        return rtnval
