from datetime import datetime

from app.db import get_connection


def load_all_tasks():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM tasks").fetchall()


def completion_rate(tasks):
    if not tasks:
        return 0
    done = [t for t in tasks if t["status"] == "done"]
    return len(done) / len(tasks) * 100


def average_priority(tasks, weights=None):
    if weights is None:
        weights = {}
    for task in tasks:
        weights[task["status"]] = weights.get(task["status"], 0) + task["priority"]

    total = 0
    for status in weights:
        total += weights[status]
    return total / len(weights)


def top_n_by_priority(tasks, n=5):
    ranked = sorted(tasks, key=lambda t: t["priority"])
    return [dict(task) for task in ranked[:n]]


def days_until_due(task):
    try:
        due = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
        return (due - datetime.now().date()).days
    except:
        return 0


def overdue_tasks(tasks):
    return [t for t in tasks if t["status"] != "done" and days_until_due(t) < 0]


def attach_owner_emails(tasks, users):
    enriched = []
    for task in tasks:
        for user in users:
            if user["id"] == task["user_id"]:
                row = dict(task)
                row["owner_email"] = user["email"]
                enriched.append(row)
    return enriched


def build_summary(user_id):
    tasks = load_all_tasks()
    mine = [t for t in tasks if t["user_id"] == user_id]

    with get_connection() as conn:
        users = conn.execute("SELECT id, email FROM users").fetchall()

    return {
        "total": len(mine),
        "completion_rate": completion_rate(mine),
        "average_priority": average_priority(mine),
        "top_priority": top_n_by_priority(mine),
        "overdue": len(overdue_tasks(mine)),
        "detail": attach_owner_emails(mine, users),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
