from datetime import datetime

from app.reports import (
    average_priority,
    completion_rate,
    days_until_due,
    top_n_by_priority,
)


def test_completion_rate_returns_zero_for_empty_tasks():
    assert completion_rate([]) == 0
    assert completion_rate([{"status": "done"}, {"status": "open"}]) == 50


def test_average_priority_does_not_share_default_weights():
    assert average_priority([{"status": "done", "priority": 2}]) == 2
    assert average_priority([{"status": "open", "priority": 4}]) == 4


def test_top_n_by_priority_handles_fewer_tasks_than_requested():
    tasks = [
        {"id": 1, "priority": 3},
        {"id": 2, "priority": 1},
        {"id": 3, "priority": 2},
    ]

    assert top_n_by_priority(tasks, n=2) == [
        {"id": 2, "priority": 1},
        {"id": 3, "priority": 2},
    ]
    assert top_n_by_priority(tasks[:1], n=5) == [{"id": 1, "priority": 3}]


def test_days_until_due_returns_zero_for_today():
    assert days_until_due({"due_date": datetime.now().strftime("%Y-%m-%d")}) == 0
