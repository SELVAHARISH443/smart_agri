import os
import sys
import importlib
import sqlite3

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, parse_cors_origins
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


def test_database_connection_is_closed_after_use(tmp_path):
    service = AuthService(database_path=tmp_path / "auth.sqlite3")

    with service.connect() as connection:
        connection.execute("SELECT 1")

    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connection.execute("SELECT 1")


def test_auth_cors_allows_local_frontend_credentials(client):
    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
    assert response.headers["Access-Control-Allow-Credentials"] == "true"


@pytest.mark.parametrize(
    ("path", "method", "headers"),
    [
        ("/api/auth/login", "POST", "content-type"),
        ("/api/auth/register", "POST", "content-type"),
        ("/api/auth/me", "GET", "authorization"),
        ("/api/auth/logout", "POST", "content-type"),
        ("/api/health", "GET", "content-type"),
        ("/api/soil/analyze", "POST", "content-type,authorization"),
        ("/api/crop/analyze", "POST", "content-type"),
        ("/api/fertilizer/recommend", "POST", "content-type"),
        ("/api/crop/season", "GET", "content-type"),
        ("/api/crops", "GET", "authorization"),
    ],
)
def test_vercel_origin_preflight_for_api_routes(client, path, method, headers):
    origin = "https://smart-agri-os7rl3dd9-selvaharish443s-projects.vercel.app"
    response = client.options(
        path,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        },
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == origin
    assert response.headers["Access-Control-Allow-Credentials"] == "true"
    assert method in response.headers["Access-Control-Allow-Methods"]
    allowed_headers = response.headers["Access-Control-Allow-Headers"].lower()
    assert all(header in allowed_headers for header in headers.split(","))


def test_cors_is_present_on_auth_error_responses(client):
    origin = "https://smart-agri-os7rl3dd9-selvaharish443s-projects.vercel.app"

    me_response = client.get("/api/auth/me", headers={"Origin": origin})
    login_response = client.post(
        "/api/auth/login",
        json={"email": "missing@example.com", "password": "securepass123"},
        headers={"Origin": origin},
    )
    register_response = client.post(
        "/api/auth/register",
        json={},
        headers={"Origin": origin},
    )

    assert me_response.status_code == 401
    assert login_response.status_code == 401
    assert register_response.status_code == 400
    for response in (me_response, login_response, register_response):
        assert response.headers["Access-Control-Allow-Origin"] == origin
        assert response.headers["Access-Control-Allow-Credentials"] == "true"


def test_cors_rejects_unconfigured_origin(client):
    response = client.get(
        "/api/health",
        headers={"Origin": "https://untrusted.example"},
    )

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response.headers


def test_cors_origin_parser_keeps_explicit_origins_only():
    assert parse_cors_origins(
        "https://stable.example, *, https://invalid.example/path"
    ) == ["https://stable.example"]


def test_auth_cookie_supports_cross_site_production_session(client, monkeypatch):
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "true")
    response = client.post(
        "/api/auth/register",
        json={"email": "cookie@example.com", "password": "securepass123"},
    )

    cookie = response.headers["Set-Cookie"]
    assert response.status_code == 201
    assert "Secure" in cookie
    assert "SameSite=None" in cookie
