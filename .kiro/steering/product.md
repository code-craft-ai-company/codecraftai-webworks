# Product Overview

codecraftai-webworks is a Python package providing web application infrastructure for the Code Craft AI ecosystem. It implements:

- ASGI application layer (HTTP handlers, WebSocket, SSE, background tasks, lifespan management)
- WSGI application layer (server, workers, middleware, request/response handling)
- Web application persona system for establishing application identity, configuration, and presence directories

The package is designed for test automation frameworks, prioritizing debuggability and readability over performance. It integrates with the broader ccai ecosystem (thisapp, testbase, configuration, credentials, dataprofiles).
