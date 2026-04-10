from __future__ import annotations

import os


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        msg = f"Environment variable {name} must be set."
        raise RuntimeError(msg)
    return value


def get_csv(name: str, default: list[str] | None = None) -> list[str]:
    raw_value = os.getenv(name)
    if not raw_value:
        return default or []
    return [item.strip() for item in raw_value.split(",") if item.strip()]
