import pytest

from tests.conftest import CREDENTIALS


@pytest.mark.parametrize("new_password", ["", "short"])
def test_password_reset_rejects_short_password_without_changing_existing_one(
    client, new_password
):
    assert client.post("/api/users/register", json=CREDENTIALS).status_code == 201
    token = client.post(
        "/api/users/forgot-password", json={"email": CREDENTIALS["email"]}
    ).get_json()["token"]

    response = client.post(
        "/api/users/reset-password",
        json={"token": token, "password": new_password},
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "password must be at least 12 characters"}
    assert client.post("/api/users/login", json=CREDENTIALS).status_code == 200
