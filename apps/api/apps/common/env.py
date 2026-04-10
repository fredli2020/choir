from __future__ import annotations

import os

TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        msg = f"Environment variable {name} must be set."
        raise RuntimeError(msg)
    return value


def get_optional_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value in (None, ""):
        return None
    return value


def get_bool(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False

    raise RuntimeError(f"Environment variable {name} must be a boolean value.")


def get_csv(name: str, default: list[str] | None = None) -> list[str]:
    raw_value = os.getenv(name)
    if not raw_value:
        return default or []
    return [item.strip() for item in raw_value.split(",") if item.strip()]
