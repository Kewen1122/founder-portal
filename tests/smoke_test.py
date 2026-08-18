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
    "app", "database", "extensions", "utils", "totp",
    "routes.auth", "routes.licenses", "routes.customers", "routes.products",
    "routes.invoices", "routes.settings", "routes.users", "routes.audit",
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
    "/invoices", "/audit-log",
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


def test_actions_write_to_audit_log(client):
    login(client)
    r = client.get("/customers/new")
    token = re.search(rb'name="csrf_token" value="([^"]+)"', r.data).group(1).decode()
    client.post(
        "/customers/new",
        data={
            "company": "CI-Auditkunde GmbH",
            "contact": "x",
            "email": "x@example.com",
            "phone": "123",
            "csrf_token": token,
        },
    )

    conn = sqlite3.connect(sys.modules["database"].DB_NAME)
    rows = conn.execute(
        "SELECT action, details, username FROM activity_log ORDER BY id"
    ).fetchall()
    conn.close()

    actions = [r[0] for r in rows]
    assert "Login" in actions
    assert "Kunde angelegt" in actions
    entry = next(r for r in rows if r[0] == "Kunde angelegt")
    assert entry[1] == "CI-Auditkunde GmbH"
    assert entry[2] == "citest"

    r = client.get("/audit-log")
    assert b"Kunde angelegt" in r.data
    assert b"CI-Auditkunde GmbH" in r.data


def test_2fa_full_lifecycle(client):
    import pyotp

    login(client)

    r = client.get("/2fa/setup")
    assert r.status_code == 200
    secret = re.search(rb'<code>([^<]+)</code>', r.data).group(1).decode()

    tok = re.search(rb'name="csrf_token" value="([^"]+)"', r.data).group(1).decode()
    r = client.post("/2fa/setup", data={"code": "000000", "csrf_token": tok})
    assert r.status_code == 302
    r = client.get("/change-password")
    assert b"Ist f\xc3\xbcr dein Konto aktiv" not in r.data, "falscher Code darf 2FA nicht aktivieren"

    valid_code = pyotp.TOTP(secret).now()
    r = client.post("/2fa/setup", data={"code": valid_code, "csrf_token": tok}, follow_redirects=True)
    assert r.status_code == 200
    assert "aktiviert".encode() in r.data

    client.get("/logout", follow_redirects=True)

    r = client.get("/login")
    tok = re.search(rb'name="csrf_token" value="([^"]+)"', r.data).group(1).decode()
    r = client.post(
        "/login", data={"username": "citest", "password": "citest-pw-123", "csrf_token": tok},
        follow_redirects=True,
    )
    assert b"Best\xc3\xa4tigungscode" in r.data, "sollte nach Passwort zum 2FA-Schritt fuehren"
    assert client.get("/dashboard").status_code == 302, "Dashboard sollte vor 2FA-Bestaetigung nicht erreichbar sein"

    tok2 = re.search(rb'name="csrf_token" value="([^"]+)"', client.get("/login/2fa").data).group(1).decode()
    client.post("/login/2fa", data={"code": "000000", "csrf_token": tok2})
    assert client.get("/dashboard").status_code == 302, "falscher 2FA-Code darf nicht einloggen"

    valid_code2 = pyotp.TOTP(secret).now()
    r = client.post(
        "/login/2fa", data={"code": valid_code2, "csrf_token": tok2}, follow_redirects=True
    )
    assert r.status_code == 200
    assert client.get("/dashboard").status_code == 200, "nach korrektem 2FA-Code sollte Dashboard erreichbar sein"


def test_founder_can_reset_other_users_2fa(client):
    import pyotp

    login(client)
    r = client.get("/2fa/setup")
    secret = re.search(rb'<code>([^<]+)</code>', r.data).group(1).decode()
    tok = re.search(rb'name="csrf_token" value="([^"]+)"', r.data).group(1).decode()
    client.post("/2fa/setup", data={"code": pyotp.TOTP(secret).now(), "csrf_token": tok}, follow_redirects=True)

    conn = sqlite3.connect(sys.modules["database"].DB_NAME)
    row = conn.execute("SELECT id, totp_secret FROM users WHERE username='citest'").fetchone()
    assert row[1], "totp_secret sollte gesetzt sein"
    uid = row[0]
    conn.close()

    r = client.get("/users")
    tok3 = re.search(rb'name="csrf_token" value="([^"]+)"', r.data).group(1).decode()
    r = client.post(
        f"/users/{uid}/reset-2fa",
        data={"csrf_token": tok3},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"zur\xc3\xbcckgesetzt" in r.data

    conn = sqlite3.connect(sys.modules["database"].DB_NAME)
    totp_secret = conn.execute("SELECT totp_secret FROM users WHERE id=?", (uid,)).fetchone()[0]
    conn.close()
    assert totp_secret is None, "totp_secret sollte nach Reset NULL sein"


def test_new_user_role_is_whitelisted(client):
    login(client)
    r = client.get("/users/new")
    tok = re.search(rb'name="csrf_token" value="([^"]+)"', r.data).group(1).decode()
    client.post(
        "/users/new",
        data={"username": "ci-eviluser", "password": "eviluser-pw-1", "role": "superadmin", "csrf_token": tok},
    )

    conn = sqlite3.connect(sys.modules["database"].DB_NAME)
    role = conn.execute("SELECT role FROM users WHERE username='ci-eviluser'").fetchone()[0]
    conn.close()
    assert role == "mitarbeiter", "unbekannte Rolle sollte auf das niedrigste Recht zurueckfallen"

    client.post(
        "/users/new",
        data={"username": "ci-founder2", "password": "founder2-pw-1", "role": "founder", "csrf_token": tok},
    )
    conn = sqlite3.connect(sys.modules["database"].DB_NAME)
    role = conn.execute("SELECT role FROM users WHERE username='ci-founder2'").fetchone()[0]
    conn.close()
    assert role == "founder"


def test_audit_log_filter_by_username(client):
    login(client)

    r = client.get("/customers/new")
    tok = re.search(rb'name="csrf_token" value="([^"]+)"', r.data).group(1).decode()
    client.post(
        "/customers/new",
        data={"company": "CI-Filter GmbH", "contact": "x", "email": "x@example.com", "phone": "1", "csrf_token": tok},
    )

    r = client.get("/audit-log?username=citest")
    assert r.status_code == 200
    assert b"Kunde angelegt" in r.data

    r = client.get("/audit-log?username=nichtvorhanden")
    assert r.status_code == 200
    assert b"Kunde angelegt" not in r.data
    assert b"Noch keine Aktivit" in r.data
