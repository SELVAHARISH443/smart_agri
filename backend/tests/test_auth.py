import os
import sys
import importlib

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from services.auth_service import AuthService, auth_service

auth_service_module = importlib.import_module("services.auth_service")


@pytest.fixture
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "auth.sqlite3"
    monkeypatch.setattr(auth_service, "database_path", str(database_path))
    auth_service.initialize_database()
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def test_register_login_and_logout(client):
    registration = client.post(
        "/api/auth/register",
        json={"email": "Farmer@example.com", "password": "securepass123"},
    )
    assert registration.status_code == 201
    assert registration.get_json()["user"]["email"] == "farmer@example.com"
    assert "HttpOnly" in registration.headers["Set-Cookie"]

    assert client.get("/api/crops").status_code == 200
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/crops").status_code == 401

    login = client.post(
        "/api/auth/login",
        json={"email": "FARMER@example.com", "password": "securepass123"},
    )
    assert login.status_code == 200
    assert client.get("/api/auth/me").get_json()["user"]["email"] == "farmer@example.com"

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_registration_validation_and_duplicate_email(client):
    invalid_password = client.post(
        "/api/auth/register",
        json={"email": "farmer@example.com", "password": "short"},
    )
    assert invalid_password.status_code == 400

    first = client.post(
        "/api/auth/register",
        json={"email": "farmer@example.com", "password": "securepass123"},
    )
    duplicate = client.post(
        "/api/auth/register",
        json={"email": "FARMER@example.com", "password": "securepass123"},
    )
    assert first.status_code == 201
    assert duplicate.status_code == 409


def test_login_rejects_invalid_password(client):
    client.post(
        "/api/auth/register",
        json={"email": "farmer@example.com", "password": "securepass123"},
    )
    client.post("/api/auth/logout")
    response = client.post(
        "/api/auth/login",
        json={"email": "farmer@example.com", "password": "wrongpass123"},
    )
    assert response.status_code == 401
    assert client.get("/api/crops").status_code == 401


def test_database_path_environment_variable_takes_precedence_and_preserves_data(
    tmp_path, monkeypatch
):
    configured_path = tmp_path / "persistent" / "auth.sqlite3"
    legacy_path = tmp_path / "legacy.sqlite3"
    monkeypatch.setenv("DATABASE_PATH", str(configured_path))
    monkeypatch.setenv("AGRI_AUTH_DB", str(legacy_path))

    service = AuthService()
    user, error = service.register("existing@example.com", "securepass123")

    assert error is None
    assert service.database_path == str(configured_path)
    assert not legacy_path.exists()

    reopened_service = AuthService()
    assert reopened_service.authenticate("existing@example.com", "securepass123") == user


def test_invalid_database_path_does_not_fall_back(tmp_path, monkeypatch):
    configured_path = tmp_path / "is-a-directory"
    configured_path.mkdir()
    fallback_path = tmp_path / "fallback.sqlite3"
    monkeypatch.setenv("DATABASE_PATH", str(configured_path))
    monkeypatch.setenv("AGRI_AUTH_DB", str(fallback_path))

    with pytest.raises(ValueError, match="is a directory"):
        AuthService()

    assert not fallback_path.exists()


def test_database_directory_permission_error_is_explicit(tmp_path, monkeypatch):
    configured_path = tmp_path / "unavailable" / "auth.sqlite3"
    fallback_path = tmp_path / "fallback.sqlite3"
    monkeypatch.setenv("DATABASE_PATH", str(configured_path))
    monkeypatch.setenv("AGRI_AUTH_DB", str(fallback_path))

    def deny_directory_creation(path, exist_ok=False):
        raise PermissionError("permission denied")

    monkeypatch.setattr(auth_service_module.os, "makedirs", deny_directory_creation)

    with pytest.raises(RuntimeError) as error:
        AuthService()

    assert str(configured_path) in str(error.value)
    assert "permission denied" in str(error.value)
    assert not fallback_path.exists()
