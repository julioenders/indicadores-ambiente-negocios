"""Fallback de secrets para CI — lê de variáveis de ambiente."""

import os

_cache: dict[str, str] = {}


def get_secret(name: str, default: str | None = None) -> str | None:
    if name in _cache:
        return _cache[name]
    value = os.getenv(name, default)
    if value is not None:
        _cache[name] = value
    return value
