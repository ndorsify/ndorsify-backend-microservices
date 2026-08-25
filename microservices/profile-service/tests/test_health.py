"""Skeleton service — verify it boots and serves the health check."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "UP"
    assert body["service"] == "profile-service"
