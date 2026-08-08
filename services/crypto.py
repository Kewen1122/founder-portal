from pathlib import Path

from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)

from config import PRIVATE_KEY, PUBLIC_KEY


def load_private_key():

    with open(PRIVATE_KEY, "rb") as f:

        return load_pem_private_key(
            f.read(),
            password=None
        )


def load_public_key():

    with open(PUBLIC_KEY, "rb") as f:

        return load_pem_public_key(
            f.read()
        )
