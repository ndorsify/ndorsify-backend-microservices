"""CORS is enabled for the browser SPA (default origin http://localhost:3000)."""


def test_allowed_origin_gets_cors_header(client):
    r = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_preflight_allows_post(client):
    r = client.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert r.status_code in (200, 204)
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_disallowed_origin_not_reflected(client):
    r = client.get("/health", headers={"Origin": "http://evil.example"})
    assert r.status_code == 200
    # Starlette only reflects allowed origins.
    assert r.headers.get("access-control-allow-origin") != "http://evil.example"
