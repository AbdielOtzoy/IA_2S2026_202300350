"""Hashing PBKDF2 y sesiones temporales en memoria."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass


ITERATIONS = 210_000


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    if not password:
        raise ValueError("La contraseña no puede estar vacía")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        ITERATIONS,
        base64.urlsafe_b64encode(salt).decode(),
        base64.urlsafe_b64encode(digest).decode(),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(digest_text.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


@dataclass
class Session:
    username: str
    expires_at: float


class SessionStore:
    def __init__(self, ttl_seconds: int = 3600) -> None:
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[str, Session] = {}

    def create(self, username: str) -> str:
        self.cleanup()
        token = secrets.token_urlsafe(32)
        self._sessions[token] = Session(username, time.time() + self.ttl_seconds)
        return token

    def get(self, token: str | None) -> Session | None:
        if not token:
            return None
        session = self._sessions.get(token)
        if session is None or session.expires_at <= time.time():
            self._sessions.pop(token, None)
            return None
        return session

    def revoke(self, token: str | None) -> None:
        if token:
            self._sessions.pop(token, None)

    def cleanup(self) -> None:
        now = time.time()
        self._sessions = {token: session for token, session in self._sessions.items() if session.expires_at > now}


def _main() -> None:
    parser = argparse.ArgumentParser(description="Genera un hash local para MediLogic")
    parser.add_argument("--hash", dest="password", required=True)
    args = parser.parse_args()
    print(hash_password(args.password))


if __name__ == "__main__":
    _main()

