import uuid
import json
import base64

from datetime import date, timedelta

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from config import PRIVATE_KEY


DURATION_PRESETS = {
    "30d": 30,
    "90d": 90,
    "180d": 180,
    "365d": 365,
    "730d": 730,
    "lifetime": None,
}


def _b64e(data):
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def issue_license(
    customer_name,
    customer_id,
    product_name,
    edition,
    valid_days,
    max_users,
    features=None,
):

    today = date.today()

    expires = None

    if valid_days is not None:
        expires = today + timedelta(days=valid_days)

    payload = {

        "license_id": str(uuid.uuid4()),

        "customer": customer_name,

        "customer_id": customer_id,

        "product": product_name,

        "edition": edition,

        "issued_at": today.isoformat(),

        "expires_at": expires.isoformat() if expires else None,

        "max_users": max_users,

        "features": features or []

    }

    payload_bytes = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True
    ).encode()

    with open(PRIVATE_KEY, "rb") as f:

        private_key = load_pem_private_key(
            f.read(),
            password=None
        )

    if not isinstance(private_key, Ed25519PrivateKey):
        raise RuntimeError("Ungültiger privater Schlüssel.")

    signature = private_key.sign(payload_bytes)

    license_key = (
        _b64e(payload_bytes)
        + "."
        + _b64e(signature)
    )

    return payload, license_key
