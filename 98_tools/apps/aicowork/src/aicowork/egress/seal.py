# -*- coding: utf-8 -*-
"""Sealed files for `below: encrypt` (export). Stdlib + one optional package.

A sealed file is what leaves when the owner chose to encrypt rather than drop:
a file above the destination's level, or the private blocks stripped from a
file that went out in plain text. Only a passphrase typed (or filed) by a
person opens it. Format (one file, binary):

    AICOWORK-SEALED-1\\n
    {"v":1,"kdf":"scrypt","n":32768,"r":8,"p":1,"salt":"<b64>","nonce":"<b64>","aad":"<rel path>"}\\n
    <AES-256-GCM ciphertext + tag>

The key is scrypt(passphrase, salt) — a fresh salt and nonce per file; the
relative path is authenticated (aad), so a sealed file cannot be renamed into
another's place unnoticed. AES-GCM comes from the `cryptography` package
(in the full tools install; absent from the stdlib-only path): without it,
encryption refuses — it never falls back to plain text.
"""
import base64
import getpass
import hashlib
import json
import os
import sys
from pathlib import Path

MAGIC = b"AICOWORK-SEALED-1\n"
SCRYPT = {"n": 2 ** 15, "r": 8, "p": 1}
SUFFIX = ".sealed"


class SealError(Exception):
    pass


def _aesgcm():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        raise SealError("encryption needs the `cryptography` package, part of the full tools install "
                        "(`pip install cryptography`, or run through `uv`: the launcher does); the stdlib-only CLI cannot encrypt — nothing was written")
    return AESGCM


def available():
    try:
        _aesgcm()
        return True
    except SealError:
        return False


def _key(passphrase, salt, n, r, p):
    return hashlib.scrypt(passphrase.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=32,
                          maxmem=128 * 1024 * 1024)


def seal(data, passphrase, aad):
    """bytes -> sealed bytes. aad is the relative path the file is bound to."""
    aes = _aesgcm()
    if not passphrase:
        raise SealError("empty passphrase")
    salt, nonce = os.urandom(16), os.urandom(12)
    key = _key(passphrase, salt, **SCRYPT)
    ct = aes(key).encrypt(nonce, data, aad.encode("utf-8"))
    head = {"v": 1, "kdf": "scrypt", **SCRYPT, "salt": base64.b64encode(salt).decode(),
            "nonce": base64.b64encode(nonce).decode(), "aad": aad}
    return MAGIC + json.dumps(head, sort_keys=True).encode() + b"\n" + ct


def unseal(blob, passphrase):
    """sealed bytes -> (bytes, header). Wrong passphrase or any tampering -> SealError."""
    aes = _aesgcm()
    if not blob.startswith(MAGIC):
        raise SealError("not a sealed AI-Cowork file")
    rest = blob[len(MAGIC):]
    line, _, ct = rest.partition(b"\n")
    try:
        head = json.loads(line)
        salt, nonce = base64.b64decode(head["salt"]), base64.b64decode(head["nonce"])
        key = _key(passphrase, salt, head["n"], head["r"], head["p"])
        return aes(key).decrypt(nonce, ct, head["aad"].encode("utf-8")), head
    except SealError:
        raise
    except Exception:
        raise SealError("cannot open: wrong passphrase, or the file was changed")


def passphrase(base, passphrase_file=None, confirm=True):
    """The owner's passphrase: from a file OUTSIDE the instance folder (the agent
    host can read everything inside it), or typed at a terminal. Never from an
    environment variable or an argument (both end up in logs and histories)."""
    base = Path(base).resolve()
    if passphrase_file:
        f = Path(passphrase_file).resolve()
        if f == base or base in f.parents:
            raise SealError("the passphrase file is inside the instance folder — the agent host can read it; keep it outside")
        if not f.is_file():
            raise SealError(f"passphrase file not found: {f}")
        pw = f.read_text(encoding="utf-8").splitlines()[0].strip() if f.read_text(encoding="utf-8").strip() else ""
        if len(pw) < 12:
            raise SealError("passphrase shorter than 12 characters")
        return pw
    if not sys.stdin.isatty():
        raise SealError("encryption needs the owner: type the passphrase at a terminal, or pass --passphrase-file "
                        "(a file outside the folder); nothing was written")
    pw = getpass.getpass("export passphrase (owner): ")
    if confirm and getpass.getpass("again: ") != pw:
        raise SealError("passphrases differ")
    if len(pw) < 12:
        raise SealError("passphrase shorter than 12 characters")
    return pw
