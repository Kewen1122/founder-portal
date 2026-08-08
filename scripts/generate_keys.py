#!/usr/bin/env python3
"""
Einmalig auszufuehren, um das Ed25519-Schluesselpaar fuer den
Lizenzgenerator zu erzeugen.

  - keys/private.pem  -> GEHEIM. Niemals committen, niemals weitergeben.
                          Damit signiert das Founder Portal Lizenzen.
  - keys/public.pem   -> Oeffentlich. Der Inhalt dieser Datei muss in
                          JEDE Lagersoftware-Kundeninstanz als
                          Umgebungsvariable LICENSE_PUBLIC_KEY eingetragen
                          werden (siehe Lagersoftware-README).

Nutzung:
    python3 scripts/generate_keys.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding, PrivateFormat, PublicFormat, NoEncryption,
)

from config import PRIVATE_KEY, PUBLIC_KEY


def main():
    PRIVATE_KEY.parent.mkdir(parents=True, exist_ok=True)

    if PRIVATE_KEY.exists() and PRIVATE_KEY.stat().st_size > 0:
        print(f"WARNUNG: {PRIVATE_KEY} existiert bereits und enthaelt Daten.")
        answer = input("Wirklich ueberschreiben? Bereits ausgestellte Lizenzen werden dadurch UNGUELTIG! (ja/nein): ")
        if answer.strip().lower() != "ja":
            print("Abgebrochen.")
            return

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    public_pem = public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

    PRIVATE_KEY.write_bytes(private_pem)
    PUBLIC_KEY.write_bytes(public_pem)

    try:
        os.chmod(PRIVATE_KEY, 0o600)
    except OSError:
        pass

    print(f"Privater Schluessel gespeichert: {PRIVATE_KEY}")
    print(f"Oeffentlicher Schluessel gespeichert: {PUBLIC_KEY}")
    print()
    print("Naechster Schritt: Inhalt von keys/public.pem als Umgebungsvariable")
    print("LICENSE_PUBLIC_KEY in jede Lagersoftware-Kundeninstanz eintragen.")


if __name__ == "__main__":
    main()
