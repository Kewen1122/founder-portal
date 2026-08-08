from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

KEY_DIR = BASE_DIR / "keys"

PRIVATE_KEY = KEY_DIR / "license_private_key.pem"

PUBLIC_KEY = KEY_DIR / "license_public_key.pem"

EXPORT_DIR = BASE_DIR / "exports" / "licenses"
