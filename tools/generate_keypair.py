#!/usr/bin/env python3

import os
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PrivateFormat,
    PublicFormat,
    NoEncryption,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_DIR = os.path.join(BASE_DIR, "keys")

os.makedirs(KEY_DIR, exist_ok=True)

PRIVATE_PATH = os.path.join(KEY_DIR, "license_private_key.pem")
PUBLIC_PATH = os.path.join(KEY_DIR, "license_public_key.pem")

private_key = Ed25519PrivateKey.generate()
public_key = private_key.public_key()

with open(PRIVATE_PATH, "wb") as f:
    f.write(
        private_key.private_bytes(
            Encoding.PEM,
            PrivateFormat.PKCS8,
            NoEncryption(),
        )
    )

with open(PUBLIC_PATH, "wb") as f:
    f.write(
        public_key.public_bytes(
            Encoding.PEM,
            PublicFormat.SubjectPublicKeyInfo,
        )
    )

print("Schlüsselpaar erzeugt.")
print(PRIVATE_PATH)
print(PUBLIC_PATH)

