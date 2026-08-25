"""End-to-end tests for dynamic-content-service (run against SQLite)."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "UP"


def test_questions_envelope_and_grouping(client):
    r = client.get("/onboard/creator/questions")
    assert r.status_code == 200
    body = r.json()

    # NDorsifyUtil envelope
    assert body["status"] == "success"
    assert body["message"] == "success"

    data = body["data"]
    # Grouped by category, first-seen order preserved (matches seed order).
    assert list(data.keys()) == ["category1", "category2", "category3", "cat2"]

    # category1 has name1 and name4; category3 has name3 and name5.
    assert [q["question"] for q in data["category1"]] == ["What is name1", "What is name4"]
    assert [q["question"] for q in data["category3"]] == ["What is name3", "What is name5"]

    # Question DTO shape.
    q = data["category1"][0]
    assert set(q.keys()) == {"question", "dataType", "options"}
    assert q["dataType"] == "String"
    assert q["options"] == ""
