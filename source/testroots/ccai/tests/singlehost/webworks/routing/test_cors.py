"""
    Unit tests for the CORSMiddleware.

    These tests cover the security-relevant behaviour of the CORS
    middleware: the wildcard/credentials combination, the Vary header,
    preflight detection and the asynchronous form.
"""

import asyncio

from ccai.webworks.routing.middleware import MiddlewarePipeline
from ccai.webworks.routing.middleware.cors import CORSMiddleware
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import Response
from ccai.webworks.templating.response import TemplateResponse


def _handler(request):
    """
        Endpoint stand-in returning a plain 200 response.
    """
    return Response(status_code=200, body=b"ok")


def test_cors_rejects_wildcard_origin_with_credentials():
    """
        allowed_origins=['*'] with allow_credentials=True is refused at
        construction.
    """
    raised = False
    try:
        CORSMiddleware(allowed_origins=["*"], allow_credentials=True)
    except ValueError:
        raised = True

    assert raised, "Expected ValueError for wildcard origin with credentials"
    return


def test_cors_allows_credentials_with_explicit_origins():
    """
        Credentials are allowed for an explicit list of origins, and only
        for a listed origin.
    """
    cors = CORSMiddleware(allowed_origins=["https://app.example"], allow_credentials=True)

    allowed = cors(Request(method="GET", path="/", headers={"Origin": "https://app.example"}), _handler)
    other = cors(Request(method="GET", path="/", headers={"Origin": "https://evil.example"}), _handler)

    assert allowed.headers.get("Access-Control-Allow-Credentials") == "true"
    assert allowed.headers.get("Access-Control-Allow-Origin") == "https://app.example"
    assert "Access-Control-Allow-Origin" not in other.headers, f"Unexpected headers {other.headers}"
    assert "Access-Control-Allow-Credentials" not in other.headers, f"Unexpected headers {other.headers}"
    return


def test_cors_adds_vary_origin_when_echoing_a_listed_origin():
    """
        A response whose Allow-Origin echoes the request origin varies on Origin.
    """
    cors = CORSMiddleware(allowed_origins=["https://app.example"])

    response = cors(Request(method="GET", path="/", headers={"Origin": "https://app.example"}), _handler)

    assert response.headers.get("Vary") == "Origin", f"Unexpected Vary {response.headers.get('Vary')!r}"
    return


def test_cors_adds_vary_origin_to_response_without_cors_headers():
    """
        With an allow-list, a response to a request without an Origin still
        varies on Origin, so a cache does not replay it to an allowed origin.
    """
    cors = CORSMiddleware(allowed_origins=["https://app.example"])

    response = cors(Request(method="GET", path="/"), _handler)

    assert response.headers.get("Vary") == "Origin", f"Unexpected Vary {response.headers.get('Vary')!r}"
    assert "Access-Control-Allow-Origin" not in response.headers
    return


def test_cors_appends_origin_to_existing_vary_header():
    """
        An existing Vary header is extended, not replaced.
    """
    cors = CORSMiddleware(allowed_origins=["https://app.example"])

    def handler(request):
        return Response(status_code=200, headers={"Vary": "Accept-Encoding"})

    response = cors(Request(method="GET", path="/", headers={"Origin": "https://app.example"}), handler)

    assert response.headers.get("Vary") == "Accept-Encoding, Origin", \
        f"Unexpected Vary {response.headers.get('Vary')!r}"
    return


def test_cors_wildcard_response_has_no_vary_origin():
    """
        With the wildcard origin every origin receives the same answer, so
        the response does not vary on Origin.
    """
    cors = CORSMiddleware(allowed_origins=["*"])

    response = cors(Request(method="GET", path="/", headers={"Origin": "https://any.example"}), _handler)

    assert response.headers.get("Access-Control-Allow-Origin") == "*"
    assert "Vary" not in response.headers, f"Unexpected Vary {response.headers.get('Vary')!r}"
    return


def test_cors_options_without_request_method_is_not_a_preflight():
    """
        An OPTIONS request without Access-Control-Request-Method reaches the handler.
    """
    cors = CORSMiddleware(allowed_origins=["https://app.example"])
    called = []

    def handler(request):
        called.append(request.method)
        return Response(status_code=200)

    response = cors(Request(method="OPTIONS", path="/", headers={"Origin": "https://app.example"}), handler)

    assert called == ["OPTIONS"], "The handler should have been called"
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    return


def test_cors_sets_headers_on_template_response():
    """
        CORS headers are applied to a TemplateResponse, which has no set_header.
    """
    cors = CORSMiddleware(allowed_origins=["https://app.example"])

    def handler(request):
        return TemplateResponse("<p>hi</p>")

    response = cors(Request(method="GET", path="/", headers={"Origin": "https://app.example"}), handler)

    assert response.headers.get("Access-Control-Allow-Origin") == "https://app.example", \
        f"Unexpected headers {response.headers}"
    return


def test_cors_runs_in_async_pipeline():
    """
        The CORS middleware works in the asynchronous pipeline.
    """
    pipeline = MiddlewarePipeline()
    pipeline.add(CORSMiddleware(allowed_origins=["https://app.example"]))

    async def handler(request):
        return Response(status_code=200, body=b"ok")

    request = Request(method="GET", path="/", headers={"Origin": "https://app.example"})
    response = asyncio.run(pipeline.execute_async(request, handler))

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.headers.get("Access-Control-Allow-Origin") == "https://app.example"
    return
