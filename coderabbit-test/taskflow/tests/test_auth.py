from app.auth import hash_password, verify_password
from tests.conftest import CREDENTIALS


def test_password_round_trip():
    encoded = hash_password("correct-horse-battery")
    assert verify_password("correct-horse-battery", encoded)
    assert not verify_password("wrong-password-here", encoded)


def test_hashes_are_salted():
    assert hash_password("same-password") != hash_password("same-password")


def test_verify_rejects_malformed_hash():
    assert not verify_password("anything", "not-a-real-hash")


def test_register_rejects_short_password(client):
    response = client.post(
        "/api/users/register", json={"email": "a@example.com", "password": "short"}
    )
    assert response.status_code == 400


def test_register_rejects_duplicate_email(client):
    assert client.post("/api/users/register", json=CREDENTIALS).status_code == 201
    assert client.post("/api/users/register", json=CREDENTIALS).status_code == 409


def test_login_returns_token(client):
    client.post("/api/users/register", json=CREDENTIALS)
    response = client.post("/api/users/login", json=CREDENTIALS)
    assert response.status_code == 200
    assert response.get_json()["token"]


def test_login_rejects_bad_password(client):
    client.post("/api/users/register", json=CREDENTIALS)
    response = client.post(
        "/api/users/login",
        json={"email": CREDENTIALS["email"], "password": "not-the-password"},
    )
    assert response.status_code == 401


def test_protected_route_requires_token(client):
    assert client.get("/api/tasks").status_code == 401
