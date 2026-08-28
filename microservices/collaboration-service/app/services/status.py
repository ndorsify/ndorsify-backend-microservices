"""Pure collaboration-status rollup — unit-tested in isolation."""
from typing import List


def next_collab_status(deliverable_statuses: List[str]) -> str:
    """Roll a collaboration's status up from its deliverables' statuses.

    accepted  — no deliverables, or all still 'todo'
    in_progress — some work started, not all submitted
    submitted — every deliverable has at least one submission
    approved  — every deliverable approved (or live)
    live      — every deliverable live
    """
    if not deliverable_statuses:
        return "accepted"

    s = deliverable_statuses
    if all(x == "live" for x in s):
        return "live"
    if all(x in ("approved", "live") for x in s):
        return "approved"
    if all(x != "todo" for x in s):
        return "submitted"
    if any(x != "todo" for x in s):
        return "in_progress"
    return "accepted"
