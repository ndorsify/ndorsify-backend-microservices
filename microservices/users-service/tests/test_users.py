"""End-to-end tests for users-service (run against SQLite)."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "UP"


def test_create_and_response_shape(client):
    r = client.post(
        "/users",
        json={
            "firstName": "Ada",
            "lastName": "Lovelace",
            "email": "ada@ndorsify.dev",
            "imageUrl": "http://img/ada.png",
            "country": "UK",  # accepted and ignored (not on entity)
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["firstName"] == "Ada"
    assert body["email"] == "ada@ndorsify.dev"
    # Response DTO exposes only these five fields.
    assert set(body.keys()) == {"id", "firstName", "lastName", "email", "imageUrl"}
    assert isinstance(body["id"], int)


def test_list_and_page_envelope(client):
    for i in range(3):
        client.post("/users", json={"firstName": f"User{i}", "email": f"u{i}@x.io"})

    # /users/list -> plain array
    r = client.get("/users/list", params={"page": 0, "size": 2, "sortBy": "id"})
    assert r.status_code == 200
    arr = r.json()
    assert isinstance(arr, list)
    assert len(arr) == 2

    # /users -> Spring-Page-shaped envelope
    r = client.get("/users", params={"page": 0, "size": 2, "sortBy": "id"})
    assert r.status_code == 200
    page = r.json()
    assert page["number"] == 0
    assert page["size"] == 2
    assert page["numberOfElements"] == 2
    assert page["totalElements"] >= 3
    assert page["first"] is True
    assert page["last"] is False
    assert len(page["content"]) == 2


def test_update_existing_and_missing(client):
    created = client.post("/users", json={"firstName": "Grace", "email": "g@x.io"}).json()
    uid = created["id"]

    r = client.put(f"/users/{uid}", json={"firstName": "Grace Hopper", "email": "gh@x.io"})
    assert r.status_code == 200
    assert r.json()["firstName"] == "Grace Hopper"
    assert r.json()["id"] == uid

    r = client.put("/users/999999", json={"firstName": "Nobody"})
    assert r.status_code == 404
