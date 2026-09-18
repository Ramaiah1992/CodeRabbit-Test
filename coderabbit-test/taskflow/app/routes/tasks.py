from flask import Blueprint, current_app, g, jsonify, request

from app.auth import login_required
from app.db import get_connection
from app.models import Task

bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")

SEARCH_SORT_COLUMNS = frozenset(
    {
        "id",
        "title",
        "description",
        "status",
        "priority",
        "due_date",
        "created_at",
    }
)
SEARCH_DIRECTIONS = frozenset({"ASC", "DESC"})


def _page_params():
    page = max(request.args.get("page", 1, type=int), 1)
    requested = request.args.get(
        "per_page", current_app.config["PAGE_SIZE_DEFAULT"], type=int
    )
    per_page = min(max(requested, 1), current_app.config["PAGE_SIZE_MAX"])
    return page, per_page


@bp.get("")
@login_required
def list_tasks():
    status = request.args.get("status")
    page, per_page = _page_params()

    sql = "SELECT * FROM tasks WHERE user_id = ?"
    params = [g.user_id]

    if status:
        if status not in Task.VALID_STATUSES:
            return jsonify(error=f"unknown status: {status}"), 400
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY priority ASC, created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return jsonify(
        tasks=[Task.from_row(row).to_dict() for row in rows],
        page=page,
        per_page=per_page,
    )


@bp.get("/search")
@login_required
def search_tasks():
    """Search the caller's own tasks by title and description."""
    query = request.args.get("q", "")
    sort = request.args.get("sort", "created_at")
    direction = request.args.get("dir", "DESC").upper()

    if sort not in SEARCH_SORT_COLUMNS:
        return jsonify(error=f"unknown sort field: {sort}"), 400
    if direction not in SEARCH_DIRECTIONS:
        return jsonify(error=f"unknown sort direction: {direction}"), 400

    try:
        requested_limit = int(
            request.args.get("limit", current_app.config["PAGE_SIZE_DEFAULT"])
        )
    except (TypeError, ValueError):
        return jsonify(error="limit must be an integer"), 400

    limit = min(max(requested_limit, 1), current_app.config["PAGE_SIZE_MAX"])
    search_pattern = f"%{query}%"

    # The parentheses around the OR matter: AND binds tighter, so without them
    # the description branch would match every user's tasks.
    sql = (
        "SELECT * FROM tasks "
        "WHERE user_id = ? AND (title LIKE ? OR description LIKE ?) "
        f"ORDER BY {sort} {direction} "
        "LIMIT ?"
    )

    with get_connection() as conn:
        rows = conn.execute(
            sql, (g.user_id, search_pattern, search_pattern, limit)
        ).fetchall()

    return jsonify(
        results=[Task.from_row(row).to_dict() for row in rows],
        count=len(rows),
    )


@bp.post("")
@login_required
def create_task():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify(error="title is required"), 400

    priority = data.get("priority", 3)
    if not isinstance(priority, int) or not (
        Task.MIN_PRIORITY <= priority <= Task.MAX_PRIORITY
    ):
        return jsonify(error="priority must be an integer between 1 and 5"), 400

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks (user_id, title, description, priority, due_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                g.user_id,
                title,
                (data.get("description") or "").strip(),
                priority,
                data.get("due_date"),
            ),
        )
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()

    return jsonify(Task.from_row(row).to_dict()), 201


@bp.get("/<int:task_id>")
@login_required
def get_task(task_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, g.user_id)
        ).fetchone()

    if row is None:
        return jsonify(error="task not found"), 404
    return jsonify(Task.from_row(row).to_dict())


@bp.patch("/<int:task_id>")
@login_required
def update_task(task_id):
    data = request.get_json(silent=True) or {}

    updates = {}
    if "title" in data:
        title = (data["title"] or "").strip()
        if not title:
            return jsonify(error="title cannot be empty"), 400
        updates["title"] = title
    if "description" in data:
        updates["description"] = (data["description"] or "").strip()
    if "status" in data:
        if data["status"] not in Task.VALID_STATUSES:
            return jsonify(error=f"unknown status: {data['status']}"), 400
        updates["status"] = data["status"]
    if "priority" in data:
        priority = data["priority"]
        if not isinstance(priority, int) or not (
            Task.MIN_PRIORITY <= priority <= Task.MAX_PRIORITY
        ):
            return jsonify(error="priority must be an integer between 1 and 5"), 400
        updates["priority"] = priority

    if not updates:
        return jsonify(error="no updatable fields supplied"), 400

    assignments = ", ".join(f"{column} = ?" for column in updates)
    params = list(updates.values()) + [task_id, g.user_id]

    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE tasks SET {assignments} WHERE id = ? AND user_id = ?", params
        )
        if cursor.rowcount == 0:
            return jsonify(error="task not found"), 404
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    return jsonify(Task.from_row(row).to_dict())


@bp.delete("/<int:task_id>")
@login_required
def delete_task(task_id):
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, g.user_id)
        )

    if cursor.rowcount == 0:
        return jsonify(error="task not found"), 404
    return "", 204
