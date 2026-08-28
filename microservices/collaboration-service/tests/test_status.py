from app.services.status import next_collab_status


def test_rollup():
    assert next_collab_status([]) == "accepted"
    assert next_collab_status(["todo", "todo"]) == "accepted"
    assert next_collab_status(["submitted", "todo"]) == "in_progress"
    assert next_collab_status(["submitted", "submitted"]) == "submitted"
    assert next_collab_status(["changes_requested", "approved"]) == "submitted"
    assert next_collab_status(["approved", "approved"]) == "approved"
    assert next_collab_status(["approved", "live"]) == "approved"
    assert next_collab_status(["live", "live"]) == "live"
