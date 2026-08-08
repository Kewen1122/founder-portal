"""Verbindet services/licensing.py (Signieren) mit der Datenbank und dem
Datei-Export. Routen sollen NICHT direkt services/licensing.py aufrufen,
sondern immer ueber diese Schicht gehen - so bleibt an einer Stelle
nachvollziehbar, wie eine Lizenz in der DB und als Datei landet.
"""
import json

from database import get_db
from services.licensing import issue_license, DURATION_PRESETS
from config import EXPORT_DIR


class LicenseServiceError(Exception):
    pass


def create_license(customer_id, product_id, duration_key, max_users, features,
                    license_type="standard"):
    db = get_db()
    try:
        customer = db.execute(
            "SELECT * FROM customers WHERE id=?", (customer_id,)
        ).fetchone()
        product = db.execute(
            "SELECT * FROM software_products WHERE id=?", (product_id,)
        ).fetchone()

        if not customer:
            raise LicenseServiceError("Kunde nicht gefunden.")
        if not product:
            raise LicenseServiceError("Produkt nicht gefunden.")
        if duration_key not in DURATION_PRESETS:
            raise LicenseServiceError("Ungueltige Laufzeit.")

        valid_days = DURATION_PRESETS[duration_key]

        payload, license_key = issue_license(
            customer_name=customer["company"],
            customer_id=customer["id"],
            product_name=product["name"],
            edition=product["edition"],
            valid_days=valid_days,
            max_users=max_users,
            features=features,
        )

        db.execute(
            """INSERT INTO licenses(
                customer_id, product_id, license_id, license_type,
                issued_at, valid_until, max_users, features_json,
                payload_json, license_key, status
            ) VALUES (?,?,?,?,?,?,?,?,?,?,'active')""",
            (
                customer_id, product_id, payload["license_id"], license_type,
                payload["issued_at"], payload["expires_at"], max_users,
                json.dumps(features or []), json.dumps(payload), license_key,
            ),
        )
        db.commit()
        row_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        db.close()

    _write_export_file(payload["license_id"], license_key)
    return row_id, payload, license_key


def _write_export_file(license_id, license_key):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / f"{license_id}.lic"
    path.write_text(license_key)
    return path


def get_license_file_path(license_id):
    return EXPORT_DIR / f"{license_id}.lic"


def list_licenses():
    db = get_db()
    try:
        rows = db.execute("""
            SELECT licenses.*, customers.company, software_products.name AS product_name,
                   software_products.edition AS product_edition
            FROM licenses
            JOIN customers ON customers.id = licenses.customer_id
            JOIN software_products ON software_products.id = licenses.product_id
            ORDER BY licenses.created_at DESC
        """).fetchall()
        return rows
    finally:
        db.close()


def get_license(license_row_id):
    db = get_db()
    try:
        return db.execute("""
            SELECT licenses.*, customers.company, software_products.name AS product_name,
                   software_products.edition AS product_edition
            FROM licenses
            JOIN customers ON customers.id = licenses.customer_id
            JOIN software_products ON software_products.id = licenses.product_id
            WHERE licenses.id=?
        """, (license_row_id,)).fetchone()
    finally:
        db.close()


def revoke_license(license_row_id):
    db = get_db()
    try:
        db.execute("UPDATE licenses SET status='revoked' WHERE id=?", (license_row_id,))
        db.commit()
    finally:
        db.close()
