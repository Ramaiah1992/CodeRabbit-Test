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
