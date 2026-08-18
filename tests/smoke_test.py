"""Automatisierter Regressionstest fuer das Founder-Portal.

Ersetzt die bisher manuell ausgefuehrten Flask-Testclient-Checks durch eine
wiederholbare Testdatei - lokal per `pytest` und in der CI (siehe
.github/workflows/ci.yml). Nutzt eine frische, leere Test-DB (kein Zugriff
auf echte Kunden-/Lizenzdaten).
"""
import re
import sqlite3
import sys
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

APP_MODULES = [
    "app", "database", "extensions",
    "routes.auth", "routes.licenses", "routes.customers", "routes.products",
    "routes.invoices", "routes.settings", "routes.users",
    "services.license_service", "services.invoice_service", "services.pdf_service",
    "services.crypto", "services.customer_service", "services.licensing",
]


@pytest.fixture()
def client(monkeypatch, tmp_path):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_path)
    monkeypatch.setenv("SECRET_KEY", "test-secret-for-ci")

    for mod in APP_MODULES:
        sys.modules.pop(mod, None)

    import app as appmod

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO users (username, password, role) VALUES (?,?,?)",
        ("citest", generate_password_hash("citest-pw-123"), "founder"),
    )
    conn.commit()
    conn.close()

    yield appmod.app.test_client()


def login(client):
    r = client.get("/login")
    token = re.search(rb'name="csrf_token" value="([^"]+)"', r.data).group(1).decode()
    r = client.post(
        "/login",
        data={"username": "citest", "password": "citest-pw-123", "csrf_token": token},
        follow_redirects=True,
    )
    assert r.status_code == 200
    return token


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_login_page_has_csrf_and_flash_support(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert b"csrf_token" in r.data


def test_failed_login_shows_message(client):
    r = client.get("/login")
    token = re.search(rb'name="csrf_token" value="([^"]+)"', r.data).group(1).decode()
    r = client.post(
        "/login",
        data={"username": "nichtvorhanden", "password": "falsch", "csrf_token": token},
    )
    assert b"alert-danger" in r.data
    assert "Benutzername oder Passwort falsch".encode() in r.data


def test_login_succeeds(client):
    login(client)


@pytest.mark.parametrize("path", [
    "/dashboard", "/customers", "/customers/new", "/products", "/products/new",
    "/licenses", "/users", "/users/new", "/settings", "/change-password",
    "/invoices",
])
def test_core_pages_render(client, path):
    login(client)
    r = client.get(path)
    assert r.status_code == 200, f"{path} lieferte {r.status_code}"


def test_customer_create_end_to_end(client):
    login(client)
    r = client.get("/customers/new")
    token = re.search(rb'name="csrf_token" value="([^"]+)"', r.data).group(1).decode()
    r = client.post(
        "/customers/new",
        data={
            "company": "CI-Testkunde GmbH",
            "contact": "Max Mustermann",
            "email": "test@example.com",
            "phone": "0123456789",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"CI-Testkunde GmbH" in r.data
