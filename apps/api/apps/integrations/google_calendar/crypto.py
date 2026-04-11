from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings


def _get_fernet() -> Fernet:
    source = (settings.GOOGLE_TOKEN_ENCRYPTION_KEY or settings.SECRET_KEY).encode("utf-8")
    derived_key = base64.urlsafe_b64encode(hashlib.sha256(source).digest())
    return Fernet(derived_key)


def encrypt_token(value: str) -> str:
    return _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_token(value: str) -> str:
    return _get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")

