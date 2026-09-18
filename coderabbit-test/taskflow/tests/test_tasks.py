def create(client, headers, **overrides):
    payload = {"title": "Write the review", "priority": 2}
    payload.update(overrides)
    return client.post("/api/tasks", json=payload, headers=headers)


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_create_and_fetch_task(client, auth_headers):
    created = create(client, auth_headers)
    assert created.status_code == 201
    task_id = created.get_json()["id"]

    fetched = client.get(f"/api/tasks/{task_id}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.get_json()["title"] == "Write the review"
    assert fetched.get_json()["status"] == "open"


def test_create_rejects_empty_title(client, auth_headers):
    assert create(client, auth_headers, title="   ").status_code == 400


def test_create_rejects_out_of_range_priority(client, auth_headers):
    assert create(client, auth_headers, priority=9).status_code == 400


def test_list_filters_by_status(client, auth_headers):
    first = create(client, auth_headers, title="Still open").get_json()["id"]
    second = create(client, auth_headers, title="Finished").get_json()["id"]
    client.patch(f"/api/tasks/{second}", json={"status": "done"}, headers=auth_headers)

    response = client.get("/api/tasks?status=open", headers=auth_headers)
    ids = [task["id"] for task in response.get_json()["tasks"]]
    assert ids == [first]


def test_list_rejects_unknown_status(client, auth_headers):
    response = client.get("/api/tasks?status=nonsense", headers=auth_headers)
    assert response.status_code == 400


def test_per_page_is_capped(client, auth_headers):
    for index in range(5):
        create(client, auth_headers, title=f"Task {index}")

    response = client.get("/api/tasks?per_page=10000", headers=auth_headers)
    assert response.get_json()["per_page"] == 100


def test_search_binds_query_and_applies_requested_order(client, auth_headers):
    create(client, auth_headers, title="Sam's low priority task", priority=4)
    create(client, auth_headers, title="Sam's high priority task", priority=1)

    response = client.get(
        "/api/tasks/search",
        query_string={"q": "Sam's", "sort": "priority", "dir": "asc"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert [task["priority"] for task in response.get_json()["results"]] == [1, 4]


def test_search_excludes_other_users_tasks(client, auth_headers):
    other_credentials = {
        "email": "other@example.com",
        "password": "another-correct-horse-battery",
    }
    assert client.post("/api/users/register", json=other_credentials).status_code == 201
    login_response = client.post("/api/users/login", json=other_credentials)
    assert login_response.status_code == 200
    other_headers = {
        "Authorization": f"Bearer {login_response.get_json()['token']}"
    }

    other_task = create(
        client, other_headers, title="Private matching task"
    ).get_json()
    response = client.get(
        "/api/tasks/search",
        query_string={"q": "Private matching task"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert other_task["id"] not in [task["id"] for task in response.get_json()["results"]]


def test_search_rejects_invalid_query_options(client, auth_headers):
    invalid_sort = client.get(
        "/api/tasks/search",
        query_string={"sort": "created_at; SELECT 1"},
        headers=auth_headers,
    )
    invalid_direction = client.get(
        "/api/tasks/search", query_string={"dir": "sideways"}, headers=auth_headers
    )
    invalid_limit = client.get(
        "/api/tasks/search", query_string={"limit": "many"}, headers=auth_headers
    )

    assert invalid_sort.status_code == 400
    assert invalid_direction.status_code == 400
    assert invalid_limit.status_code == 400


def test_search_limit_is_clamped(client, auth_headers, app):
    app.config["PAGE_SIZE_MAX"] = 2
    for index in range(3):
        create(client, auth_headers, title=f"Matching task {index}")

    response = client.get(
        "/api/tasks/search",
        query_string={"q": "Matching", "limit": 1000},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.get_json()["count"] == 2


def test_update_and_delete(client, auth_headers):
    task_id = create(client, auth_headers).get_json()["id"]

    updated = client.patch(
        f"/api/tasks/{task_id}", json={"status": "in_progress"}, headers=auth_headers
    )
    assert updated.get_json()["status"] == "in_progress"

    assert client.delete(f"/api/tasks/{task_id}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/tasks/{task_id}", headers=auth_headers).status_code == 404


def test_missing_task_returns_404(client, auth_headers):
    assert client.get("/api/tasks/9999", headers=auth_headers).status_code == 404
